# Licensed under a 3-clause BSD style license - see LICENSE.rst
import inspect

import asv_env_pixi
from asv_env_pixi import Pixi, _find_pixi_bin


def test_tool_name():
    assert Pixi.tool_name == "pixi"


def test_not_a_rattler_alias():
    src = inspect.getsource(asv_env_pixi)
    assert "asv_env_rattler" not in src
    assert "pixi.toml" in src or "_write_manifest" in src
    assert "_find_pixi_bin" in src


def test_find_pixi_and_matches():
    path = _find_pixi_bin()
    # may be present on developer machines
    result = Pixi.matches("3.12")
    assert result is (path is not None)
    assert Pixi.matches("not-a-version") is False


def test_entry_point_metadata():
    from importlib.metadata import entry_points

    eps = entry_points()
    try:
        group = list(eps.select(group="asv.environment_backends"))
    except AttributeError:
        group = list(eps.get("asv.environment_backends", []))
    names = {ep.name: ep.value for ep in group if ep.name == "pixi"}
    assert "pixi" in names
    assert "asv_env_pixi" in names["pixi"]
