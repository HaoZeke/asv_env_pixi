# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""pip+ matrix keys must not be silently dropped."""

from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import asv_env_pixi
from asv_env_pixi import Pixi


def test_source_installs_or_declares_pip_plus():
    src = Path(asv_env_pixi.__file__).read_text()
    assert "pip+" in src
    assert "pypi-dependencies" in src
    assert "_install_pip_requirements" in src
    assert "construct_pip_call" in src


def test_partition_and_manifest_include_pypi(tmp_path, monkeypatch):
    monkeypatch.setattr(asv_env_pixi, "_find_pixi_bin", lambda: "/usr/bin/true")
    conf = SimpleNamespace(
        env_dir=str(tmp_path / "env"),
        project="p",
        repo=".",
        repo_subdir="",
        install_timeout=60,
        default_benchmark_timeout=60,
        conda_channels=["conda-forge"],
        matrix={},
        pythons=["3.12"],
        build_command=[],
        install_command=[],
        uninstall_command=[],
    )
    # Bypass Environment.__init__ heavy path by constructing carefully
    env = object.__new__(Pixi)
    env._python = "3.12"
    env._requirements = {"numpy": "1.26", "pip+requests": "2.31"}
    env._base_requirements = {}
    env._channels = ["conda-forge"]
    env._path = str(tmp_path / "ws")
    env._pixi = "/usr/bin/true"
    env._pixi_env_prefix = str(tmp_path / "ws" / ".pixi" / "envs" / "default")
    conda, pip = env._partition_requirements()
    assert ("numpy", "1.26") in conda
    assert ("requests", "2.31") in pip
    manifest = env._write_manifest()
    text = Path(manifest).read_text()
    assert "[pypi-dependencies]" in text
    assert "requests" in text
    assert "numpy" in text
    assert "pip+requests" not in text  # key prefix stripped
