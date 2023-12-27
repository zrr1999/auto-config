from __future__ import annotations

from collections.abc import Sequence

from loguru import logger

from ..device import Device
from ..field import DefaultExtraField, SSHHostField
from .base import GeneratorBase


class SSHHostsGenerator(GeneratorBase):
    def __init__(self, devices: Sequence[Device[DefaultExtraField]]):
        super().__init__()
        self.devices = devices

    def add_host(self, host_name: str, host_domain: str, desc: str, ssh_field: SSHHostField):
        self.add_block(f"Host {host_name}", "\n", indentation=2)
        self.add_line(f"HostName {host_domain}")
        self.add_line(f"Port {ssh_field.port}")
        self.add_line(f"User {ssh_field.user}")
        self.add_line(f"ForwardAgent {"yes" if ssh_field.forward_agent else "no"}")
        self.add_line(f"#_Desc {desc}")

    def generate(self):
        for device in self.devices:
            if device.extra.ssh is None:
                logger.warning(f"device {device} has no ssh config")
                continue
            domain = f"{device.get_domain()}.bone6.top"
            self.add_host(device.get_name(), domain, device.desc, device.extra.ssh)
            logger.debug(f"added host {device.get_name()} to ssh config")
            for container in device.extra.ssh.containers:
                name = container.name or f"{device.get_name()}-{container.port}"
                self.add_host(name, domain, f"{device.desc}: {name} 容器", container)
                logger.debug(f"added container host {name} to ssh config")

        super().generate()
