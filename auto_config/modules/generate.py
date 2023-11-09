from __future__ import annotations
from typing import Sequence
from pydantic import BaseModel, Field, ValidationError
from loguru import logger
from sys import stdout
import re
import json
import toml
import os


class BaseExtraField(BaseModel):
    pass


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


class CodeGenerator:
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
            assert (
                self.generated_code is not None
            ), "generate() should set self.generated_code"

        return self.generated_code

    def write(self, path: str):
        path = os.path.expanduser(path)
        path = os.path.expandvars(path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        logger.info(f"writed to {path}")
        open(path, "w").write(self.code)


def get_devices[T: BaseExtraField](
    devices_config: list[dict], extra_field_cls: type[T] = BaseExtraField
) -> list[Device[T]]:
    devices = []
    for device in devices_config:
        try:
            extra_field_cls.model_validate(device.get("extra", {}))
            devices.append(Device[extra_field_cls].model_validate(device))
        except ValidationError:
            logger.warning(f"device {device} has invalid extra field")
            continue
    return devices


class SSHField(BaseModel):
    port: int
    user: str
    forward_agent: bool = True


class AnsibleField(BaseModel):
    aliases: list[str] = Field(default_factory=list)


class DNSField(BaseModel):
    target: str


class ExtraField(BaseExtraField):
    ssh: SSHField | None = None
    ansible: AnsibleField | None = None
    dns: DNSField | None = None


class SSHHostsGenerator(CodeGenerator):
    def __init__(self, devices: Sequence[Device[ExtraField]]):
        super().__init__()
        self.devices = devices

    def generate(self):
        for device in self.devices:
            if device.extra.ssh is None:
                logger.warning(f"device {device} has no ssh config")
                continue
            self.add_line(f"Host {device.get_name()}")
            self.add_line(f"  HostName {device.get_target()}.ssh.bone6.top")
            self.add_line(f"  Port {device.extra.ssh.port}")
            self.add_line(f"  User {device.extra.ssh.user}")
            self.add_line(
                f"  ForwardAgent {"yes" if device.extra.ssh.forward_agent else "no"}"
            )
            self.add_line(f"  #_Desc {device.desc}")
            self.add_line()


class AnsibleHostsGenerator(CodeGenerator):
    def __init__(self, devices: Sequence[Device[ExtraField]]):
        super().__init__()
        self.devices = devices

    def generate(self):
        hosts = {}
        for dev in self.devices:
            hosts.setdefault(dev.group, [])
            hosts[dev.group].append(dev.get_name())
            if dev.extra.ansible is not None:
                for alias in dev.extra.ansible.aliases:
                    hosts.setdefault(alias, [])
                    hosts[alias].append(dev.get_name())

        for group, hosts in hosts.items():
            self.add_line(f"[{group}]")
            for host in hosts:
                self.add_line(host)
            self.add_line()


# class CaddyFileGenerator(CodeGenerator):
#     def __init__(self, devices: Sequence[Device[ExtraField]]):
#         super().__init__()
#         self.devices = devices

#     def generate(self):
#         hosts = {}
#         for dev in self.devices:
#             hosts.setdefault(dev.group, [])
#             hosts[dev.group].append(dev.get_name())
#             if dev.extra.ansible is not None:
#                 for alias in dev.extra.ansible.aliases:
#                     hosts.setdefault(alias, [])
#                     hosts[alias].append(dev.get_name())

#         for group, hosts in hosts.items():
#             self.add_line(f"[{group}]")
#             for host in hosts:
#                 self.add_line(host)
#             self.add_line()


class DNSConfigGenerator(CodeGenerator):
    def __init__(self, devices: Sequence[Device[ExtraField]]):
        super().__init__()
        self.devices = devices

    def generate(self):
        record_list = []
        for device in self.devices:
            name = device.get_target()
            if device.extra.dns is not None:
                target = device.extra.dns.target
                if re.match(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", target):
                    record_type = "A"
                else:
                    record_type = "CNAME"
            else:
                target = "0.0.0.0"
                record_type = "A"
            if device.main:
                record_list.append((device.group, "CNAME", f"{name}.bone6.top"))
            record_list.append((f"{name}", record_type, target))

        self.generated_code = json.dumps(
            {"domain": "bone6.top", "records": record_list}, indent=2
        )


def generate_config(
    path: str = "~/.config/autoconfig/config.toml", *, log_level="INFO"
):
    logger.remove()
    logger.add(stdout, level=log_level)
    path = os.path.expanduser(path)
    path = os.path.expandvars(path)
    config = toml.load(open(path, "r"))
    devices = get_devices(config["devices"], ExtraField)
    generator = AnsibleHostsGenerator(devices)
    generator.write("~/.config/ansible/hosts")
    generator = SSHHostsGenerator(devices)
    generator.write("~/.ssh/config")
    generator = DNSConfigGenerator(devices)
    generator.write("~/.config/autoconfig/dns.json")
