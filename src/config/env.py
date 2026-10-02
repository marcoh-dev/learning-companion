"""Read the environment-dependent settings from the process environment and `.env`."""

from collections.abc import Mapping, Sequence
from pathlib import Path

from environ import Env


def read_settings(environ: Mapping[str, str], env_file: Path, argv: Sequence[str]) -> dict:
    """Return `SECRET_KEY`, `DEBUG` and `ALLOWED_HOSTS` for `config.settings`."""

    class _Env(Env):
        ENVIRON = dict(environ)

    env = _Env()
    return {"SECRET_KEY": env.str("SECRET_KEY")}
