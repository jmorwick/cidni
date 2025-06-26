"""
Copyright © 2025 Joseph Kendall-Morwick

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import click
import os
from cidnilib import FileBasedDataService

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

@main.command()
@click.pass_context
@click.argument("path", metavar="<file path>")
@click.option('-r', '--recursive', is_flag=True, help="If set, target is treated as a directory and all files in this directory and its subdirectories are stored")
def know(ctx, path, recursive: bool = False):
    """Store data in specified file"""
    dataservice = ctx.obj["DATASERVICE"]

    def store_file(file_path):
        with open(file_path, 'rb') as f:
            cid, isnew = dataservice.know_file(f)
        if not isnew:
            click.echo("ALREADY STORED", err=True)
        click.echo(f"'{file_path}' --> '{cid}'")
        return cid, isnew

    if recursive and os.path.isdir(path):
        savedfiles = 0
        existingfiles = 0
        for dirpath, _, filenames in os.walk(path):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                cid, isnew = store_file(file_path)
                if isnew:
                    savedfiles += 1
                else: 
                    existingfiles += 1
        
        click.echo(f"new files: {savedfiles}", err=True)
        click.echo(f"already stored files: {existingfiles}", err=True)
    else:
        store_file(path)

@main.command()
@click.pass_context
@click.argument("cid", metavar="<content-id>")
def recall(ctx, cid):
    """Retrieve data"""
    click.echo(ctx.obj["DATASERVICE"].recall(cid))

@main.command()
@click.pass_context
@click.argument("cid", metavar="<content-id>")
def forget(ctx, cid):
    """Forget data"""
    click.echo(ctx.obj["DATASERVICE"].forget(cid))

@main.command()
@click.pass_context
def list(ctx):
    """list all known CID's"""
    for cid in ctx.obj["DATASERVICE"].list_known_cids():
        click.echo(cid)

if __name__ == "__main__":
    main()
