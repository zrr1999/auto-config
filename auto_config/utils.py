from __future__ import annotations

import os
from sys import stdout

import toml
from loguru import logger
from pydantic import ValidationError

from .device import Device
from .field import BaseExtraField, DefaultExtraField
from .generator import AnsibleHostsGenerator, DNSConfigGenerator, SSHHostsGenerator


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


def generate_config(path: str = "~/.config/autoconfig/config.toml", *, log_level="INFO"):
    logger.remove()
    logger.add(stdout, level=log_level)
    path = os.path.expanduser(path)
    path = os.path.expandvars(path)
    config = toml.load(open(path, "r"))
    devices = get_devices(config["devices"], DefaultExtraField)
    generator = AnsibleHostsGenerator(devices)
    generator.write("~/.config/ansible/hosts")
    generator = SSHHostsGenerator(devices)
    generator.write("~/.ssh/config")
    generator = DNSConfigGenerator(devices)
    generator.write("~/.config/autoconfig/auto-dns.json")
