from __future__ import annotations

import pytest

from auto_config.service import Service


@pytest.mark.benchmark
def test_get_domain():
    service = Service(name="name1", group="group1", target="target1")
    assert service.get_domain() == "name1.group1"
