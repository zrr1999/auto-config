from __future__ import annotations

from pydantic import BaseModel


class Service(BaseModel):
    name: str
    group: str
    target: str

    def get_domain(self):
        return f"{self.name}.{self.group}"
