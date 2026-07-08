# asv_env_pixi

Drop-in ASV backend for `environment_type = "pixi"`.

Creates environments by writing a minimal `pixi.toml` workspace and running
the **pixi CLI** (`pixi install`). This is intentionally CLI-subprocess
driven (not a maturin/rattler-crate wheel). For crate-backed conda creates
use `asv_env_rattler`.

## Drop-in setup

```bash
# install pixi: https://pixi.sh  (or set PIXI_EXE)
pip install asv
pip install "git+https://github.com/HaoZeke/asv_env_pixi.git"
# or: pip install -e .
```

```json
{
  "environment_type": "pixi",
  "conda_channels": ["conda-forge"],
  "pythons": ["3.12"],
  "matrix": {
    "req": {
      "numpy": ["1.26"]
    }
  },
  "install_command": [
    "in-dir={env_dir} python -mpip install --no-deps {wheel_file}"
  ]
}
```

## Capabilities

| Flag | Value |
|------|-------|
| `matrix_install_mode` | `create` |
| `supports_joint_pypi_conda_solve` | `True` (pixi can; ASV does not yet pass the project wheel into that solve) |
| `project_install_prefers_no_deps` | `True` |
| `requires_host_tool` | `pixi` |

## Discovery

```toml
[project.entry-points."asv.environment_backends"]
pixi = "asv_env_pixi:Pixi"
```

## Tests

```bash
pip install -e ".[test]"
pytest -q
```
