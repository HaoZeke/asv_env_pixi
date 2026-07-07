# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""ASV ``environment_type="pixi"`` backend via the **pixi** CLI workspace model.

This is **not** a thin alias of ``asv_env_rattler``. It creates a real pixi
workspace (``pixi.toml``), runs ``pixi install``, and executes Python from
``.pixi/envs/default`` — the same layout developers use with the pixi tool.

Locate the binary via ``PIXI_EXE``, ``PATH``, or the default install path
``~/.pixi/bin/pixi`` (official installer). The unrelated PyPI project named
``pixi`` is **not** used.
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
    env = os.environ.get("PIXI_EXE")
    if env and os.path.isfile(env) and os.access(env, os.X_OK):
        return env
    which = shutil.which("pixi")
    if which:
        return which
    # Official installer default
    home = Path.home() / ".pixi" / "bin" / ("pixi.exe" if WIN else "pixi")
    if home.is_file() and os.access(home, os.X_OK):
        return str(home)
    return None


class Pixi(environment.Environment):
    """Manage an ASV env as a pixi workspace + default environment prefix."""

    tool_name = "pixi"

    def __init__(self, conf, python, requirements, tagged_env_vars):
        self._python = python
        self._requirements = requirements
        self._channels = list(getattr(conf, "conda_channels", None) or [])
        if "conda-forge" not in self._channels:
            self._channels.append("conda-forge")
        self._pixi = _find_pixi_bin()
        if not self._pixi:
            raise environment.EnvironmentUnavailable(
                "asv_env_pixi requires the pixi CLI (install from https://pixi.sh "
                "or set PIXI_EXE); the unrelated PyPI package named 'pixi' is not used"
            )
        super().__init__(conf, python, requirements, tagged_env_vars)
        # Populated after _setup
        self._pixi_env_prefix = os.path.join(self._path, ".pixi", "envs", "default")

    @classmethod
    def matches(cls, python):
        if not (re.match(r"^[0-9].*$", python) or re.match(r"^pypy[0-9.]*$", python)):
            return False
        return _find_pixi_bin() is not None

    def _pixi_env(self):
        env = dict(os.environ)
        env.update(self.build_env_vars)
        return env

    def _run_pixi(self, args, **kwargs):
        env = kwargs.pop("env", None) or self._pixi_env()
        timeout = kwargs.pop("timeout", self._install_timeout)
        return util.check_output(
            [self._pixi] + list(args), env=env, timeout=timeout, **kwargs
        )

    def _write_manifest(self) -> Path:
        """Write a minimal pixi.toml for this ASV environment matrix cell."""
        root = Path(self._path)
        root.mkdir(parents=True, exist_ok=True)
        deps = [f'python = "=={self._python}.*"' if "." in self._python else f'python = "{self._python}"']
        # Prefer equality-ish pins for MAJOR.MINOR ASV python strings
        if re.match(r"^\d+\.\d+$", self._python):
            deps = [f'python = "{self._python}.*"']
        else:
            deps = [f'python = "{self._python}"']
        deps.append('pip = "*"')
        deps.append('wheel = "*"')

        pypi_deps = []
        for key, val in {**self._requirements, **self._base_requirements}.items():
            if key.startswith("pip+"):
                name = key[4:]
                pin = f'=={val}' if val else "*"
                pypi_deps.append(f'{name} = "{pin}"' if val else f'{name} = "*"')
            else:
                if val:
                    deps.append(f'{key} = "{val}"')
                else:
                    deps.append(f'{key} = "*"')

        channels = ", ".join(f'"{c}"' for c in self._channels)
        # Single current platform — ASV envs are host-local
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
        body = textwrap.dedent(
            f"""\
            [workspace]
            name = "asv-env"
            channels = [{channels}]
            platforms = ["{plat}"]

            [dependencies]
            """
        )
        body += "\n".join(deps) + "\n"
        if pypi_deps:
            body += "\n[pypi-dependencies]\n"
            body += "\n".join(pypi_deps) + "\n"

        manifest = root / "pixi.toml"
        manifest.write_text(body, encoding="utf-8")
        return manifest

    def _setup(self):
        log.info(f"Creating pixi workspace for {self.name} via {self._pixi}")
        manifest = self._write_manifest()
        # Install default environment into .pixi/envs/default under self._path
        util.check_call(
            [
                self._pixi,
                "install",
                "--manifest-path",
                str(manifest),
            ],
            env=self._pixi_env(),
            cwd=self._path,
            timeout=self._install_timeout,
        )
        prefix = Path(self._pixi_env_prefix)
        if not prefix.is_dir():
            # Some pixi versions may use a different default env name
            envs_root = Path(self._path) / ".pixi" / "envs"
            if envs_root.is_dir():
                kids = [p for p in envs_root.iterdir() if p.is_dir()]
                if kids:
                    self._pixi_env_prefix = str(kids[0])
                    prefix = Path(self._pixi_env_prefix)
        py = prefix / ("python.exe" if WIN else "bin/python")
        if not py.exists() and not (prefix / "bin" / "python").exists():
            raise environment.EnvironmentUnavailable(
                f"pixi install finished but no python under {self._pixi_env_prefix}"
            )
        log.info(f"pixi default env at {self._pixi_env_prefix}")

    def find_executable(self, executable):
        prefix = getattr(self, "_pixi_env_prefix", None) or os.path.join(
            self._path, ".pixi", "envs", "default"
        )
        if WIN:
            paths = [
                prefix,
                os.path.join(prefix, "Scripts"),
                os.path.join(prefix, "bin"),
            ]
        else:
            paths = [os.path.join(prefix, "bin")]
        return util.which(executable, paths)

    def run_executable(self, executable, args, **kwargs):
        # Mirror Environment.run_executable but PATH the pixi env prefix
        env = kwargs.pop("env", os.environ).copy()
        env.update(self._global_env_vars)
        if "PATH" in env:
            paths = env["PATH"].split(os.pathsep)
        else:
            paths = []
        prefix = getattr(self, "_pixi_env_prefix", None) or os.path.join(
            self._path, ".pixi", "envs", "default"
        )
        if WIN:
            for sub in ["Library\\mingw-w64\\bin", "Library\\bin", "Library\\usr\\bin", "Scripts"]:
                paths.insert(0, os.path.join(prefix, sub))
            paths.insert(0, prefix)
        else:
            paths.insert(0, os.path.join(prefix, "bin"))
        if "ASV_PYTHONPATH" in env:
            env["PYTHONPATH"] = env["ASV_PYTHONPATH"]
            env.pop("ASV_PYTHONPATH", None)
        else:
            env.pop("PYTHONPATH", None)
        kwargs["env"] = dict(env, PIP_USER="false", PATH=str(os.pathsep.join(paths)))
        exe = self.find_executable(executable)
        if kwargs.get("timeout", None) is None:
            kwargs["timeout"] = self._install_timeout
        return util.check_output([exe] + list(args), **kwargs)

    def run(self, args, **kwargs):
        log.debug(f"Running '{' '.join(args)}' in {self.name}")
        return self.run_executable("python", args, **kwargs)

    def _run_pip(self, args, **kwargs):
        return self.run_executable("python", ["-m", "pip"] + list(args), **kwargs)


__all__ = ["Pixi", "_find_pixi_bin"]
