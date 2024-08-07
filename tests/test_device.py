from __future__ import annotations

from auto_config.device import Device


def test_get_name():
    device = Device(system="system1", hardware="hardware1", group="group1", desc="")
    assert device.get_name() == "group1-hardware1-system1"


def test_get_domain():
    device = Device(system="system1", hardware="hardware1", group="group1", desc="")
    assert device.get_domain() == "hardware1-system1.ssh.group1"
