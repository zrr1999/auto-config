from __future__ import annotations

import os

from loguru import logger


class Block:
    def __init__(self, start_line: str = "", end_line: str = "", *, indentation: int = 0):
        self.start_line = start_line
        self.end_line = end_line
        self.indentation = indentation
        self._lines: list[str] = []

    def add_line(self, line: str = ""):
        self._lines.append(f"{' '*self.indentation}{line}")

    def generate(self):
        return "\n".join([self.start_line, *self._lines, self.end_line])


class GeneratorBase:
    def __init__(self):
        self._generated_code: str | None = None
        self._cur_block = Block("", "")
        self._block: list[Block] = [self._cur_block]

    def add_block(self, start_line: str = "", end_line: str = "", *, indentation: int = 0):
        self._cur_block = Block(start_line, end_line, indentation=indentation)
        self._block.append(self._cur_block)
        # return

    def add_line(self, line: str = ""):
        self._cur_block.add_line(line)

    def generate(self):
        self._generated_code = "\n".join(block.generate() for block in self._block)

    def clear(self):
        self._generated_code = None

    @property
    def code(self):
        if self._generated_code is None:
            self.generate()
            assert self._generated_code is not None, "generate() should set self._generated_code"

        return self._generated_code

    def write(self, path: str):
        path = os.path.expanduser(path)
        path = os.path.expandvars(path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(self.code)
        logger.info(f"writed to {path}")
