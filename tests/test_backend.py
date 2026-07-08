# Licensed under a 3-clause BSD style license - see LICENSE.rst
import ast
from pathlib import Path

import asv_env_pixi
from asv_env_pixi import Pixi, _HAS_RATTLER


def test_tool_name():
    assert Pixi.tool_name == "pixi"


def test_uses_rattler_not_cli_only():
    tree = ast.parse(Path(asv_env_pixi.__file__).read_text())
    imported = []
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module:
            imported.append(n.module)
        elif isinstance(n, ast.Import):
            imported.extend(a.name for a in n.names)
    assert any(m == "rattler" or m.startswith("rattler.") for m in imported)
    src = Path(asv_env_pixi.__file__).read_text()
    assert "shutil.which" not in src or "pixi" not in src.split("shutil.which")[0][-20:]
    # no pixi CLI driver
    assert "_find_pixi_bin" not in src
    assert "pixi install" not in src or "not" in src.lower()


def test_matches():
    if _HAS_RATTLER:
        assert Pixi.matches("3.12") is True
    else:
        assert Pixi.matches("3.12") is False
    assert Pixi.matches("nope") is False


def test_entry_point_metadata():
    from importlib.metadata import entry_points

    eps = entry_points()
    try:
        group = list(eps.select(group="asv.environment_backends"))
    except AttributeError:
        group = list(eps.get("asv.environment_backends", []))
    names = {ep.name: ep.value for ep in group if ep.name == "pixi"}
    assert "pixi" in names
