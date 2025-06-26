"""
Copyright © 2025 Joseph Kendall-Morwick

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import click
from cidnilib import FileBasedDataService

@click.group(invoke_without_command=True)
@click.option('--dataservice', envvar="CIDNI_DATASERVICE", help="Specify data service (defaults to CIDNI_DATASERVICE)")
@click.pass_context
def main(ctx, dataservice):
    """Cidni CLI – requires a command to follow cidni"""
    if ctx.invoked_subcommand is None:
        click.echo("Error: Missing command\n", err=True)
        click.echo(ctx.get_help())
        ctx.exit(1)
    ctx.ensure_object(dict)
    ctx.obj["DATASERVICE"] = FileBasedDataService(dataservice)

@main.command()
@click.pass_context
@click.argument("path", metavar="<file path>")
def know(ctx, path):
    """Store data in specified file"""
    cid, isnew = ctx.obj["DATASERVICE"].know_file(open(path, 'rb'))
    if isnew: click.echo("Stored as {cid}".format(cid=cid))
    else: click.echo("Already stored as {cid}".format(cid=cid))

@main.command()
@click.pass_context
@click.argument("cid", metavar="<content-id>")
def recall(ctx, cid):
    """Retrieve data"""
    click.echo(ctx.obj["DATASERVICE"].recall(cid))

if __name__ == "__main__":
    main()
