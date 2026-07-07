# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import tempfile
from pathlib import Path

import pytest

from asv.config import Config
from asv_env_pixi import Pixi, _find_pixi_bin


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


def test_create_pixi_workspace_has_python(conf):
    if _find_pixi_bin() is None:
        pytest.skip("pixi not available")
    os.chdir(tempfile.mkdtemp())
    import sys

    py = f"{sys.version_info.major}.{sys.version_info.minor}"
    env = Pixi(conf, py, {}, {})
    Path(env._path).mkdir(parents=True, exist_ok=True)
    env._setup()
    py_path = Path(env.find_executable("python"))
    assert py_path.exists()
    assert ".pixi" in str(py_path) or (Path(env._path) / ".pixi").exists()
    out = env.run_executable("python", ["-c", "print(2+2)"])
    assert "4" in out
