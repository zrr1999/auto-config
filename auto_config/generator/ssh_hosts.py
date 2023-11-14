from __future__ import annotations

from typing import Sequence

from loguru import logger

from ..device import Device
from ..field import DefaultExtraField
from .base import GeneratorBase


class SSHHostsGenerator(GeneratorBase):
    def __init__(self, devices: Sequence[Device[DefaultExtraField]]):
        super().__init__()
        self.devices = devices

    def generate(self):
        for device in self.devices:
            if device.extra.ssh is None:
                logger.warning(f"device {device} has no ssh config")
                continue
            self.add_line(f"Host {device.get_name()}")
            self.add_line(f"  HostName {device.get_target()}.bone6.top")
            self.add_line(f"  Port {device.extra.ssh.port}")
            self.add_line(f"  User {device.extra.ssh.user}")
            self.add_line(f"  ForwardAgent {"yes" if device.extra.ssh.forward_agent else "no"}")
            self.add_line(f"  #_Desc {device.desc}")
            self.add_line()
