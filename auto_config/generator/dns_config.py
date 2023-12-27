from __future__ import annotations

import json
from collections.abc import Sequence

from ..device import Device
from ..field import DefaultExtraField
from .base import GeneratorBase


class DNSConfigGenerator(GeneratorBase):
    def __init__(self, devices: Sequence[Device[DefaultExtraField]]):
        super().__init__()
        self.devices = devices

    def generate(self):
        record_list = []
        for device in self.devices:
            name = device.get_domain()
            target = device.extra.dns.public if device.extra.dns is not None else "unknown"
            if device.extra.ansible is not None and device.extra.ansible.server:
                record_list.append((device.group, f"{name}.bone6.top"))
            record_list.append((f"{name}", target))

        self._generated_code = json.dumps({"domain": "bone6.top", "records": record_list}, indent=2)
