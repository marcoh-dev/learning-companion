"""Read the environment-dependent settings from the process environment and `.env`."""

from collections.abc import Mapping, Sequence
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from environ import Env

# Only ever used for local development and tests; never deploy with it.
DEV_SECRET_KEY = "django-insecure-dev-only-blaty8p0xz6oj7k2n6ktocoazl5ey7ov5jdlxsly"


def read_settings(environ: Mapping[str, str], env_file: Path, argv: Sequence[str]) -> dict:
    """Return `SECRET_KEY`, `DEBUG` and `ALLOWED_HOSTS` for `config.settings`."""

    class _Env(Env):
        ENVIRON = dict(environ)

    env = _Env()
    debug = env.bool("DEBUG", default=False)
    secret_key = env.str("SECRET_KEY", default="")
    if not secret_key:
        if not debug:
            raise ImproperlyConfigured(
                "Set the SECRET_KEY environment variable (or add it to .env); "
                "the development key is only used when DEBUG is True."
            )
        secret_key = DEV_SECRET_KEY
    return {
        "SECRET_KEY": secret_key,
        "DEBUG": debug,
        "ALLOWED_HOSTS": env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"]),
    }
