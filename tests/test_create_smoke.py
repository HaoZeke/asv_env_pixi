# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import tempfile
from pathlib import Path

import pytest

from asv.config import Config
from asv_env_pixi import Pixi, _HAS_RATTLER


@pytest.fixture
def conf(tmp_path):
    c = Config()
    c.env_dir = str(tmp_path / "env")
    c.project = "smoke"
    c.repo = str(tmp_path / "repo")
    c.repo_subdir = ""
    c.install_timeout = 900.0
    c.default_benchmark_timeout = 60.0
    c.conda_channels = ["conda-forge"]
    c.conda_environment_file = "IGNORE"
    c.matrix = {}
    return c


def test_create_via_py_rattler_pixi_layout(conf):
    if not _HAS_RATTLER:
        pytest.skip("py-rattler not installed")
    os.chdir(tempfile.mkdtemp())
    import sys

    py = f"{sys.version_info.major}.{sys.version_info.minor}"
    env = Pixi(conf, py, {}, {})
    Path(env._path).mkdir(parents=True, exist_ok=True)
    env._setup()
    assert (Path(env._path) / "pixi.toml").is_file()
    assert Path(env.find_executable("python")).exists()
    assert ".pixi" in str(env.find_executable("python"))
    out = env.run_executable("python", ["-c", "print(4*4)"])
    assert "16" in out
