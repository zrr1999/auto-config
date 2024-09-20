from __future__ import annotations

from sys import stdout
from typing import Optional

import typer
from loguru import logger

from auto_config import utils

app = typer.Typer()


@app.command()
def generate_config(
    path: str = typer.Argument("~/.config/autoconfig/config.toml"),
    *,
    groups: Optional[list[str]] = None,
    log_level="INFO",
):
    logger.remove()
    logger.add(stdout, level=log_level)
    utils.generate_config(path, groups=groups)


if __name__ == "__main__":
    app()
