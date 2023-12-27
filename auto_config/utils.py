from __future__ import annotations

import os
from sys import stdout

import toml
from loguru import logger
from pydantic import ValidationError

from .device import Device
from .field import BaseExtraField, DefaultExtraField
from .generator import AnsibleHostsGenerator, DNSConfigGenerator, SSHHostsGenerator
from .service import Service


def get_devices[T: BaseExtraField](
    devices_config: list[dict], extra_field_cls: type[T] = BaseExtraField
) -> list[Device[T]]:
    devices = []
    for device in devices_config:
        try:
            extra_field_cls.model_validate(device.get("extra", {}))
            devices.append(Device[extra_field_cls].model_validate(device))
        except ValidationError as e:
            logger.warning(f"device has invalid extra field: {e}")
            continue
    return devices


def get_services(services_config: list[dict]) -> list[Service]:
    services = []
    for service in services_config:
        services.append(Service.model_validate(service))
    return services


def generate_config(path: str = "~/.config/autoconfig/config.toml", *, log_level="INFO"):
    logger.remove()
    logger.add(stdout, level=log_level)
    path = os.path.expanduser(path)
    path = os.path.expandvars(path)
    with open(path) as f:
        config = toml.load(f)
    devices = get_devices(config["devices"], DefaultExtraField)
    generator = AnsibleHostsGenerator(devices)
    generator.write("~/.config/ansible/hosts")
    generator = SSHHostsGenerator(devices)
    generator.write("~/.ssh/config")
    generator = DNSConfigGenerator(devices)
    generator.write("~/.config/autoconfig/auto-ddns.json")
