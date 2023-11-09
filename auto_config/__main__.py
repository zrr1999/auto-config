from __future__ import annotations
from loguru import logger
from sys import stdout
import typer
from auto_config.modules import generate, update_dnspod

app = typer.Typer()


@app.command()
def generate_config(
    path: str = "~/.config/autoconfig/config.toml", *, log_level="INFO"
):
    logger.remove()
    logger.add(stdout, level=log_level)
    generate.generate_config(path)


@app.command()
def update_records_from_json(
    path: str = "~/.config/autoconfig/config.toml", *, log_level="INFO"
):
    logger.remove()
    logger.add(stdout, level=log_level)
    update_dnspod.update_records_from_json(path)


if __name__ == "__main__":
    app()
