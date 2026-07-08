# asv_env_pixi

ASV `environment_type = "pixi"` via the **pixi CLI** (subprocess).

This is **not** a maturin wheel over rattler crates. For Rust-crate-backed
conda-ecosystem creates, use **asv_env_rattler**.

```bash
# install pixi: https://pixi.sh
pip install "git+https://github.com/HaoZeke/asv_env_pixi.git"
```

```json
{ "environment_type": "pixi" }
```
