"""
Copyright © 2025 Joseph Kendall-Morwick

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import click
import os
import stat
import sniffpy
from cidnilib import FileBasedDataService, InMemoryKnowledgeService, PickleFileBasedDataService, typers, archive_typers, extractors

@click.group(invoke_without_command=True)
@click.option('--dataservice', envvar="CIDNI_DATASERVICE", help="Specify data service (defaults to CIDNI_DATASERVICE)")
@click.pass_context
def main(ctx, dataservice):
    """Cidni CLI requires a command to follow cidni"""
    if ctx.invoked_subcommand is None:
        click.echo("Error: Missing command\n", err=True)
        click.echo(ctx.get_help())
        ctx.exit(1)
    ctx.ensure_object(dict)
    ctx.obj["DATASERVICE"] = FileBasedDataService(dataservice)
    ds_for_ks = PickleFileBasedDataService(dataservice, levels=0)
    ctx.obj["KNOWLEDGESERVICE"] = InMemoryKnowledgeService(ds_for_ks)
    ctx.call_on_close(ds_for_ks.close)

@main.command()
@click.pass_context
@click.argument("path", metavar="<file path>")
@click.option('-r', '--recursive', is_flag=True, help="If set, target is treated as a directory and all files in this directory and its subdirectories are stored")
def know(ctx, path, recursive: bool = False):
    """Store data in specified file"""
    dataservice = ctx.obj["DATASERVICE"]
    knowledgeservice = ctx.obj["KNOWLEDGESERVICE"]

    def store_file(file_path):
        with open(file_path, 'rb') as f:
            cid, isnew = dataservice.know_file(f)
        if not isnew:
            click.echo("ALREADY STORED", err=True)

        click.echo(f"'{file_path}' --> '{dataservice.encode(cid)}'")
        acid, known = knowledgeservice.believe(dataservice.encode(cid), 'had_path', file_path)
        stats = os.stat(file_path)
        click.echo(f"storing last_accessed {stats.st_atime}", err=True)
        knowledgeservice.believe(dataservice.encode(acid), 'last_accessed', str(stats.st_atime))
        click.echo(f"storing last_modified {stats.st_mtime}", err=True)
        knowledgeservice.believe(dataservice.encode(acid), 'last_modified', str(stats.st_mtime))
        click.echo(f"storing created {stats.st_ctime}", err=True)
        knowledgeservice.believe(dataservice.encode(acid), 'created', str(stats.st_ctime))
        
        try:
            with open(file_path, "rb") as f:
                mime = sniffpy.sniff(f.read())
            knowledgeservice.believe(dataservice.encode(cid), 'mime_type', mime.type)
            knowledgeservice.believe(dataservice.encode(cid), 'mime_subtype', mime.subtype)
        except: 
            click.echo('sniffpy error', err=True)
            knowledgeservice.believe(dataservice.encode(cid), 'mime_type', 'error')
        return cid, isnew

    if recursive and os.path.isdir(path):
        savedfiles = 0
        existingfiles = 0
        skippedfiles = 0
        for dirpath, _, filenames in os.walk(path):
            if stat.S_ISDIR(os.stat(dirpath).st_mode): 
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    try: 
                        if stat.S_ISREG(os.stat(file_path).st_mode): 
                            cid, isnew = store_file(file_path)
                            if isnew and cid:
                                savedfiles += 1
                            elif cid: 
                                existingfiles += 1
                        else:
                            click.echo("Invalid Path: " + file_path + " ...skipping", err=True)
                            skippedfiles += 1
                    except:
                        click.echo("Invalid Path: " + file_path + " ...skipping", err=True)
                        skippedfiles += 1
        click.echo(f"new files: {savedfiles}", err=True)
        click.echo(f"already stored files: {existingfiles}", err=True)
        click.echo(f"skipped files: {skippedfiles}", err=True)
    elif not os.path.islink(path): 
        store_file(path)
    else:
        click.echo('skipping symbolic link')

@main.command()
@click.pass_context
@click.argument("cid", metavar="<content-id>")
def recall(ctx, cid):
    """Retrieve data"""
    click.echo(ctx.obj["DATASERVICE"].recall_text(cid))

@main.command()
@click.pass_context
@click.argument("cid", metavar="<content-id>")
def forget(ctx, cid):
    """Forget data"""
    click.echo(ctx.obj["DATASERVICE"].forget(cid))

@main.command()
@click.pass_context
@click.argument("cid", metavar="<content-id>")
def confirm(ctx, cid):
    """Confirm cid for stored data (check for errors in storage)"""
    dstream = ctx.obj["DATASERVICE"].recall_stream(cid)
    ncid, updated = ctx.obj["DATASERVICE"].know_file(dstream)
    if ctx.obj["DATASERVICE"].encode(ncid) == cid and not updated:
        click.echo('identity confirmed')
    else:
        click.echo('error: ' + cid + ' != ' + ctx.obj["DATASERVICE"].encode(ncid))

@main.command()
@click.pass_context
@click.option('-p', '--property', help="only enumerate data with the indicated property/value")
def list(ctx, property):
    """list all known CID's"""
    v = None
    p = property
    if property and property.find('=') > 0:
        p, v = property.split('=')
        i = ctx.obj["KNOWLEDGESERVICE"].inquire(None, p, v)
        for cid, _, _ in i:
            click.echo(cid)
    else:
        for ecid in ctx.obj["DATASERVICE"].list_known_cids():
            click.echo(ctx.obj["DATASERVICE"].encode(ecid))

@main.command()
@click.pass_context
@click.argument("cid", metavar="<content-id>")
def extract(ctx, cid):
    """extract and know all contents of archive identified by cid"""
    ds = ctx.obj["DATASERVICE"]
    ks = ctx.obj["KNOWLEDGESERVICE"]
    type = None
    for t in archive_typers:
        if typers[t](ctx.obj["DATASERVICE"].recall_stream(cid)):
            type = t
    if not type:
        raise click.BadParameter("CID must represent an archive of a known type", ctx)
    ex = extractors[type]
    ex(ds, ks, cid)


if __name__ == "__main__":
    main()
