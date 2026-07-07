# Licensed under a 3-clause BSD style license - see LICENSE.rst
import ast
import inspect
from pathlib import Path

import asv_env_pixi
from asv_env_pixi import Pixi, _find_pixi_bin


def test_tool_name():
    assert Pixi.tool_name == "pixi"


def test_not_a_rattler_alias():
    """Must not import or subclass asv_env_rattler (docstring may mention it)."""
    src_path = Path(asv_env_pixi.__file__)
    tree = ast.parse(src_path.read_text(encoding="utf-8"))
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported.append(node.module)
    assert not any("rattler" in name for name in imported)
    src = inspect.getsource(Pixi)
    assert "_write_manifest" in inspect.getsource(asv_env_pixi)
    assert "_find_pixi_bin" in inspect.getsource(asv_env_pixi)
    assert "pixi install" in inspect.getsource(asv_env_pixi) or "install" in src


def test_find_pixi_and_matches():
    path = _find_pixi_bin()
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


def test_write_manifest_smoke(tmp_path):
    p = object.__new__(Pixi)
    p._python = "3.12"
    p._requirements = {"numpy": "1.26"}
    p._base_requirements = {}
    p._channels = ["conda-forge"]
    p._path = str(tmp_path)
    manifest = Pixi._write_manifest(p)
    text = manifest.read_text(encoding="utf-8")
    assert "python" in text
    assert "numpy" in text
    assert "[workspace]" in text or "channels" in text
