import importlib.util
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

from config.env import read_settings

REPO_ROOT = Path(settings.BASE_DIR).parent
REQUIREMENTS_PATH = REPO_ROOT / "requirements.txt"


class RequirementsTests(SimpleTestCase):
    def test_django_environ_is_pinned_and_importable(self):
        lines = REQUIREMENTS_PATH.read_text().splitlines()

        self.assertIn("django-environ==0.14.0", lines)
        self.assertIsNotNone(importlib.util.find_spec("environ"))


MISSING_ENV_FILE = REPO_ROOT / "does-not-exist" / ".env"
RUNSERVER_ARGV = ["manage.py", "runserver"]


def read(environ=None, env_file=MISSING_ENV_FILE, argv=RUNSERVER_ARGV):
    return read_settings(environ or {}, env_file, argv)


class ReadSettingsTests(SimpleTestCase):
    def test_secret_key_is_taken_from_the_environment(self):
        result = read({"SECRET_KEY": "from-env"})

        self.assertEqual(result["SECRET_KEY"], "from-env")
