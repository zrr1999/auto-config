from __future__ import annotations

from typing import Sequence

from ..device import Device
from ..field import DefaultExtraField
from .base import GeneratorBase


class CaddyFileGenerator(GeneratorBase):
    def __init__(self, devices: Sequence[Device[DefaultExtraField]]):
        super().__init__()
        self.devices = devices

    # def generate(self):
    #     hosts = {}
    #     for dev in self.devices:
    #         hosts.setdefault(dev.group, [])
    #         hosts[dev.group].append(dev.get_name())
    #         if dev.extra.ansible is not None:
    #             for alias in dev.extra.ansible.aliases:
    #                 hosts.setdefault(alias, [])
    #                 hosts[alias].append(dev.get_name())

    #     for group, hosts in hosts.items():
    #         self.add_line(f"[{group}]")
    #         for host in hosts:
    #             self.add_line(host)
    #         self.add_line()
