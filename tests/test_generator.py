from __future__ import annotations

import pytest

from auto_config.generator import (
    AnsibleHostsGenerator,
    CaddyFileGenerator,
    DNSConfigGenerator,
    GeneratorBase,
    SSHHostsGenerator,
)


@pytest.mark.benchmark
def test_generator_base():
    generator = GeneratorBase()
    generator.add_line("line1")
    generator.add_block(start_line="start1", end_line="end1")
    generator.add_line("line2")
    assert generator.code == "\nline1\n\nstart1\nline2\nend1"
    generator.clear()
    assert generator._generated_code is None
    assert generator.code == "\nline1\n\nstart1\nline2\nend1"
    # generator.write("path")


@pytest.mark.benchmark
def test_generator_init():
    devices = []
    AnsibleHostsGenerator(devices).generate()
    SSHHostsGenerator(devices).generate()
    CaddyFileGenerator(devices).generate()
    DNSConfigGenerator(devices).generate()
