from __future__ import annotations

import json
import re
from typing import Sequence

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

        self.generated_code = json.dumps({"domain": "bone6.top", "records": record_list}, indent=2)
