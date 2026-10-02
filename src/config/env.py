"""Read the environment-dependent settings from the process environment and `.env`."""

from collections.abc import Mapping, Sequence
from pathlib import Path

from environ import Env

# Only ever used for local development and tests; never deploy with it.
DEV_SECRET_KEY = "django-insecure-dev-only-blaty8p0xz6oj7k2n6ktocoazl5ey7ov5jdlxsly"


def read_settings(environ: Mapping[str, str], env_file: Path, argv: Sequence[str]) -> dict:
    """Return `SECRET_KEY`, `DEBUG` and `ALLOWED_HOSTS` for `config.settings`."""

    class _Env(Env):
        ENVIRON = dict(environ)

    env = _Env()
    debug = env.bool("DEBUG", default=False)
    return {
        "SECRET_KEY": env.str("SECRET_KEY", default=DEV_SECRET_KEY),
        "DEBUG": debug,
        "ALLOWED_HOSTS": env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"]),
    }
