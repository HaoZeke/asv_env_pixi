# Licensed under a 3-clause BSD style license - see LICENSE.rst
import ast
from pathlib import Path

import asv_env_pixi
from asv_env_pixi import Pixi, _find_pixi_bin


def test_tool_name():
    assert Pixi.tool_name == "pixi"


def test_is_cli_subprocess_not_maturin_rattler():
    root = Path(__file__).resolve().parents[1]
    assert not (root / "Cargo.toml").exists()
    src = Path(asv_env_pixi.__file__).read_text()
    assert "_find_pixi_bin" in src
    assert "pixi install" in src or '"install"' in src
    tree = ast.parse(src)
    imported = []
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module:
            imported.append(n.module)
    assert not any(m == "rattler" or m.startswith("rattler.") for m in imported)


def test_matches():
    assert Pixi.matches("not-a-version") is False
    r = Pixi.matches("3.12")
    assert r is (_find_pixi_bin() is not None)


def test_entry_point_metadata():
    from importlib.metadata import entry_points

    eps = entry_points()
    try:
        group = list(eps.select(group="asv.environment_backends"))
    except AttributeError:
        group = list(eps.get("asv.environment_backends", []))
    assert any(ep.name == "pixi" for ep in group)

