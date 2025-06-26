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
