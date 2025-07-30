"""
Main entry point for the Corrupt Video Inspector application.

This module allows the package to be executed as:
    python -m src.main
    python src/main.py
"""

import logging
from pathlib import Path

import click

from .cli.main import cli
from .config.config import load_config


@click.group(invoke_without_command=True)
@click.version_option(
    prog_name="corrupt-video-inspector",
    message="%(prog)s %(version)s",
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=Path),
    default=Path("config.yaml"),
    show_default=True,
    help="Path to the configuration YAML file.",
)
@click.pass_context
def main(ctx: click.Context, config_path: Path) -> None:
    """
    CLI entry point for Corrupt Video Inspector.

    Args:
        ctx (click.Context): Click context.
        config_path (Path): Path to the YAML configuration file.
    """
    config = load_config(config_path)
    logging.basicConfig(
        level=getattr(logging, config.logging.level.upper(), logging.WARNING),
        filename=str(config.logging.file),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt=config.logging.date_format,
    )
    logging.info("Starting Corrupt Video Inspector...")
    ctx.obj = ctx.obj or {}
    ctx.obj["config"] = config
    # If no subcommand, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


main.add_command(cli)

if __name__ == "__main__":
    main()
