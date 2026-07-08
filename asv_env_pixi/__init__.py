# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""ASV ``environment_type="pixi"`` via the **pixi CLI** (subprocess).

Primary create path: locate a real ``pixi`` binary, write a minimal workspace
manifest, run ``pixi install``, use ``.pixi/envs/default``.

This is intentionally **not** a maturin/rattler-crate native core. For
Rust-crate-backed conda-ecosystem creates use ``asv_env_rattler``.
"""

from __future__ import annotations

import os
import re
import shutil
import textwrap
from pathlib import Path

from asv import environment, util
from asv.console import log

WIN = os.name == "nt"


def _find_pixi_bin() -> str | None:
    for key in ("PIXI_EXE", "ASV_PIXI_BIN"):
        val = os.environ.get(key)
        if val and os.path.isfile(val) and os.access(val, os.X_OK):
            return val
    which = shutil.which("pixi")
    if which:
        return which
    home = Path.home() / ".pixi" / "bin" / ("pixi.exe" if WIN else "pixi")
    if home.is_file() and os.access(home, os.X_OK):
        return str(home)
    return None


class Pixi(environment.Environment):
    """Manage an ASV env with the pixi CLI (subprocess-driven)."""

    tool_name = "pixi"
    matrix_install_mode = "create"
    supports_joint_pypi_conda_solve = True
    supports_joint_pypi_solve = True
    project_install_prefers_no_deps = True
    requires_host_tool = "pixi"

    def __init__(self, conf, python, requirements, tagged_env_vars):
        self._python = python
        self._requirements = requirements
        self._channels = list(getattr(conf, "conda_channels", None) or [])
        if "conda-forge" not in self._channels:
            self._channels.append("conda-forge")
        self._pixi = _find_pixi_bin()
        if not self._pixi:
            raise environment.EnvironmentUnavailable(
                "asv_env_pixi requires the pixi CLI (https://pixi.sh or PIXI_EXE). "
                "This package is CLI-subprocess driven, not a maturin/rattler wheel."
            )
        super().__init__(conf, python, requirements, tagged_env_vars)
        self._pixi_env_prefix = os.path.join(self._path, ".pixi", "envs", "default")

    @classmethod
    def matches(cls, python):
        if not (re.match(r"^[0-9].*$", python) or re.match(r"^pypy[0-9.]*$", python)):
            return False
        return _find_pixi_bin() is not None

    def _write_manifest(self) -> Path:
        root = Path(self._path)
        root.mkdir(parents=True, exist_ok=True)
        import platform as _plat

        machine = _plat.machine().lower()
        system = _plat.system().lower()
        if system == "linux":
            plat = "linux-64" if machine in ("x86_64", "amd64") else f"linux-{machine}"
        elif system == "darwin":
            plat = "osx-arm64" if machine in ("arm64", "aarch64") else "osx-64"
        elif system == "windows":
            plat = "win-64"
        else:
            plat = "linux-64"
        channels = ", ".join(f'"{c}"' for c in self._channels)
        dep_lines = [
            f'python = "{self._python}.*"' if re.match(r"^\d+\.\d+$", self._python) else f'python = "{self._python}"',
            'pip = "*"',
            'wheel = "*"',
        ]
        for key, val in {**self._requirements, **getattr(self, "_base_requirements", {})}.items():
            if key.startswith("pip+"):
                continue
            dep_lines.append(f'{key} = "{val}"' if val else f'{key} = "*"')
        body = textwrap.dedent(
            f"""\
            [workspace]
            name = "asv-pixi-env"
            channels = [{channels}]
            platforms = ["{plat}"]

            [dependencies]
            """
        )
        body += "\n".join(dep_lines) + "\n"
        manifest = root / "pixi.toml"
        manifest.write_text(body, encoding="utf-8")
        return manifest

    def _setup(self):
        log.info(f"Creating pixi workspace for {self.name} via CLI {self._pixi}")
        manifest = self._write_manifest()
        util.check_call(
            [self._pixi, "install", "--manifest-path", str(manifest)],
            env={**os.environ, **self.build_env_vars},
            cwd=self._path,
            timeout=self._install_timeout,
        )
        prefix = Path(self._pixi_env_prefix)
        if not prefix.is_dir():
            envs_root = Path(self._path) / ".pixi" / "envs"
            if envs_root.is_dir():
                kids = [p for p in envs_root.iterdir() if p.is_dir()]
                if kids:
                    self._pixi_env_prefix = str(kids[0])
                    prefix = Path(self._pixi_env_prefix)
        if not (prefix / "bin" / "python").exists() and not (prefix / "python.exe").exists():
            raise environment.EnvironmentUnavailable(
                f"pixi install finished but no python under {self._pixi_env_prefix}"
            )

    def find_executable(self, executable):
        prefix = self._pixi_env_prefix
        if WIN:
            paths = [prefix, os.path.join(prefix, "Scripts"), os.path.join(prefix, "bin")]
        else:
            paths = [os.path.join(prefix, "bin")]
        return util.which(executable, paths)

    def run_executable(self, executable, args, **kwargs):
        env = kwargs.pop("env", os.environ).copy()
        env.update(self._global_env_vars)
        paths = env.get("PATH", "").split(os.pathsep) if env.get("PATH") else []
        prefix = self._pixi_env_prefix
        if WIN:
            for sub in ["Library\\mingw-w64\\bin", "Library\\bin", "Library\\usr\\bin", "Scripts"]:
                paths.insert(0, os.path.join(prefix, sub))
            paths.insert(0, prefix)
        else:
            paths.insert(0, os.path.join(prefix, "bin"))
        env.pop("PYTHONPATH", None)
        kwargs["env"] = dict(env, PIP_USER="false", PATH=str(os.pathsep.join(paths)))
        exe = self.find_executable(executable)
        if kwargs.get("timeout", None) is None:
            kwargs["timeout"] = self._install_timeout
        return util.check_output([exe] + list(args), **kwargs)

    def run(self, args, **kwargs):
        return self.run_executable("python", args, **kwargs)

    def _run_pip(self, args, **kwargs):
        return self.run_executable("python", ["-m", "pip"] + list(args), **kwargs)


__all__ = ["Pixi", "_find_pixi_bin"]
