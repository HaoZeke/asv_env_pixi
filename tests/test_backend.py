# Licensed under a 3-clause BSD style license - see LICENSE.rst
import ast
from pathlib import Path

import asv_env_pixi
from asv_env_pixi import Pixi, _HAS_RATTLER


def test_tool_name():
    assert Pixi.tool_name == "pixi"


def test_uses_rattler_api_not_pixi_cli():
    tree = ast.parse(Path(asv_env_pixi.__file__).read_text())
    imported = []
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module:
            imported.append(n.module)
        elif isinstance(n, ast.Import):
            imported.extend(a.name for a in n.names)
    assert any(m == "rattler" or m.startswith("rattler.") for m in imported)
    src = Path(asv_env_pixi.__file__).read_text()
    assert "_find_pixi_bin" not in src
    assert "shutil.which" not in src
    assert "await solve" in src or "await solve(" in src or "solve(**" in src
    assert "await install" in src or "install(records" in src


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
