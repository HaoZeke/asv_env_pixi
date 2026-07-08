# Licensed under a 3-clause BSD style license - see LICENSE.rst
from asv_env_pixi import Pixi


def test_capability_attrs():
    assert Pixi.matrix_install_mode == 'create'
    assert Pixi.supports_joint_pypi_conda_solve is True
    assert Pixi.project_install_prefers_no_deps is True
    assert Pixi.requires_host_tool == 'pixi'

