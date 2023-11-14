from __future__ import annotations

from sys import stdout

import typer
from loguru import logger

from auto_config import utils

app = typer.Typer()


@app.command()
def generate_config(path: str = "~/.config/autoconfig/config.toml", *, log_level="INFO"):
    logger.remove()
    logger.add(stdout, level=log_level)
    utils.generate_config(path)


if __name__ == "__main__":
    app()
