from __future__ import annotations

from collections.abc import Sequence

from ..device import Device
from ..field import DefaultExtraField
from .base import GeneratorBase


class AnsibleHostsGenerator(GeneratorBase):
    def __init__(self, devices: Sequence[Device[DefaultExtraField]]):
        super().__init__()
        self.devices = devices

    def generate(self):
        group_hosts: dict[str, list] = {}
        for dev in self.devices:
            group_hosts.setdefault(dev.group, [])
            group_hosts[dev.group].append(dev.get_name())
            if dev.extra.ansible is not None:
                if dev.extra.ansible.server:
                    group_hosts.setdefault("servers", [])
                    group_hosts["servers"].append(dev.get_name())
                    group_hosts.setdefault(f"server-{dev.group}", [])
                    group_hosts[f"server-{dev.group}"].append(dev.get_name())
                for alias in dev.extra.ansible.aliases:
                    group_hosts.setdefault(alias, [])
                    group_hosts[alias].append(dev.get_name())

        for group, hosts in group_hosts.items():
            self.add_line(f"[{group}]")
            for host in hosts:
                self.add_line(host)
            self.add_line()
        super().generate()
