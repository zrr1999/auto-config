from __future__ import annotations

from pydantic import BaseModel, Field

from .field import BaseExtraField


class Device[ExtraT: BaseExtraField](BaseModel):
    system: str
    hardware: str
    group: str
    main: bool = False
    desc: str = Field("")

    extra: ExtraT = Field(default_factory=BaseExtraField)

    def get_name(self):
        return f"{self.group}-{self.hardware}-{self.system}"

    def get_target(self):
        return f"{self.hardware}-{self.system}.ssh.{self.group}"
