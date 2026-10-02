"""Read the environment-dependent settings from the process environment and `.env`."""

from collections.abc import Mapping, Sequence
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from environ import Env

# Only ever used for local development and tests; never deploy with it.
DEV_SECRET_KEY = "django-insecure-dev-only-blaty8p0xz6oj7k2n6ktocoazl5ey7ov5jdlxsly"

# Publicly known keys (the .env.example value, Django's insecure keys) count as unset.
PLACEHOLDER_SECRET_KEY = "change-me"
INSECURE_KEY_PREFIX = "django-insecure-"


def read_settings(environ: Mapping[str, str], env_file: Path, argv: Sequence[str]) -> dict:
    """Return `SECRET_KEY`, `DEBUG` and `ALLOWED_HOSTS` for `config.settings`."""

    class _Env(Env):
        ENVIRON = dict(environ)

    # Fills `_Env.ENVIRON` without overwriting it, so the real environment wins.
    # A missing .env is normal (CI, production), so don't let environ log about it.
    if env_file.is_file():
        _Env.read_env(env_file)
    env = _Env()
    debug = env.bool("DEBUG", default=False)
    # Read raw: env.str() would resolve a leading `$` as a reference to another variable.
    secret_key = env.ENVIRON.get("SECRET_KEY", "")
    if _is_placeholder(secret_key):
        running_tests = (
            len(argv) > 1 and Path(argv[0]).name == "manage.py" and argv[1] == "test"
        )
        if not (debug or running_tests):
            raise ImproperlyConfigured(
                "Set the SECRET_KEY environment variable (or add it to .env) to a real, "
                "non-placeholder key; "
                "the development key is only used when DEBUG is True or under `manage.py test`."
            )
        secret_key = DEV_SECRET_KEY
    return {
        "SECRET_KEY": secret_key,
        "DEBUG": debug,
        "ALLOWED_HOSTS": [
            host.strip()
            for host in env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
            if host.strip()
        ],
    }


def _is_placeholder(secret_key: str) -> bool:
    return (
        not secret_key
        or secret_key == PLACEHOLDER_SECRET_KEY
        or secret_key.startswith(INSECURE_KEY_PREFIX)
    )
