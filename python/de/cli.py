import subprocess

import click

from de.config import Config, PROJECT_ROOT


@click.group()
@click.pass_context
def cli(ctx):
    ctx.config = Config.load()


@cli.command()
def format():
    subprocess.run(["black", PROJECT_ROOT])


@cli.command()
def lint():
    subprocess.run(["flake8", PROJECT_ROOT])


if __name__ == "__main__":
    cli()
