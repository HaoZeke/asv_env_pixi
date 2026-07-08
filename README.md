# asv_env_pixi

ASV `environment_type = "pixi"` using the **py-rattler** Rust stack
(maturin wheel from prefix.dev) — the same solver/installer family as pixi.

- Create: in-process `rattler.solve` + `rattler.install`
- Layout: `.pixi/envs/default` + a marker `pixi.toml` (documentation only)
- **Not** a wrapper around the `pixi` CLI
- **Not** the unrelated PyPI package named `pixi`

```bash
pip install "git+https://github.com/HaoZeke/asv_env_pixi.git"
```

```json
{ "environment_type": "pixi" }
```
