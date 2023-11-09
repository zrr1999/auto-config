from __future__ import annotations

from pydantic import BaseModel, Field


class BaseExtraField(BaseModel):
    pass


class SSHField(BaseModel):
    port: int
    user: str
    forward_agent: bool = True


class AnsibleField(BaseModel):
    aliases: list[str] = Field(default_factory=list)


class DNSField(BaseModel):
    target: str


class DefaultExtraField(BaseExtraField):
    ssh: SSHField | None = None
    ansible: AnsibleField | None = None
    dns: DNSField | None = None
