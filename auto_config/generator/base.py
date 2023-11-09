from __future__ import annotations

import os

from loguru import logger


class GeneratorBase:
    def __init__(self):
        self.generated_code: str | None = None

    def add_line(self, line: str = "", *, indentation: int = 0):
        if self.generated_code is None:
            self.generated_code = ""
        self.generated_code += f"{' '*indentation}{line}\n"

    def generate(self):
        raise NotImplementedError("generate() should be implemented by subclass")

    def clear(self):
        self.generated_code = None

    @property
    def code(self):
        if self.generated_code is None:
            self.generate()
            assert self.generated_code is not None, "generate() should set self.generated_code"

        return self.generated_code

    def write(self, path: str):
        path = os.path.expanduser(path)
        path = os.path.expandvars(path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        logger.info(f"writed to {path}")
        open(path, "w").write(self.code)
