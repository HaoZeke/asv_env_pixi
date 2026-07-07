# asv_env_pixi

ASV environment backend for `environment_type = "pixi"`.

Uses the real **pixi CLI** (from [pixi.sh](https://pixi.sh) / `~/.pixi/bin/pixi`,
or `PIXI_EXE`): writes a `pixi.toml` workspace under the ASV env directory,
runs `pixi install`, and runs Python from `.pixi/envs/default`.

This is **not** a rename of the rattler backend and does **not** use the
unrelated PyPI project named `pixi`.

There is no in-tree ASV `pixi` plugin; this package is the primary provider
for this type under Stage-1 discovery.

## Stage-1 discovery

```toml
[project.entry-points."asv.environment_backends"]
pixi = "asv_env_pixi:Pixi"
```

```bash
# install pixi itself first: https://pixi.sh
pip install "git+https://github.com/HaoZeke/asv_env_pixi.git"
```

```json
{ "environment_type": "pixi" }
```

## Tests

```bash
pip install -e ".[test]"
pytest -q
```
