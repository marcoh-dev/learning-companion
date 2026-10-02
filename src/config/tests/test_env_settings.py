import importlib.util
import os
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from config.env import DEV_SECRET_KEY, read_settings

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

    def test_debug_is_parsed_as_a_boolean(self):
        cases = {"True": True, "true": True, "1": True, "yes": True,
                 "False": False, "false": False, "0": False, "no": False}

        for raw, expected in cases.items():
            with self.subTest(DEBUG=raw):
                result = read({"SECRET_KEY": "k", "DEBUG": raw})
                self.assertIs(result["DEBUG"], expected)

    def test_debug_defaults_to_false(self):
        result = read({"SECRET_KEY": "k"})

        self.assertIs(result["DEBUG"], False)

    def test_allowed_hosts_is_parsed_as_a_comma_separated_list(self):
        result = read({"SECRET_KEY": "k", "ALLOWED_HOSTS": "example.com,www.example.com"})

        self.assertEqual(result["ALLOWED_HOSTS"], ["example.com", "www.example.com"])

    def test_allowed_hosts_defaults_to_localhost(self):
        result = read({"SECRET_KEY": "k"})

        self.assertEqual(result["ALLOWED_HOSTS"], ["localhost", "127.0.0.1"])

    def test_insecure_dev_key_is_used_when_secret_key_is_unset_and_debug_is_on(self):
        result = read({"DEBUG": "True"})

        self.assertEqual(result["SECRET_KEY"], DEV_SECRET_KEY)
        self.assertTrue(DEV_SECRET_KEY.startswith("django-insecure-"))

    def test_missing_secret_key_with_debug_off_is_improperly_configured(self):
        with self.assertRaisesMessage(ImproperlyConfigured, "SECRET_KEY"):
            read({"DEBUG": "False"})

    def test_test_command_uses_the_dev_key_when_secret_key_is_unset_and_debug_is_off(self):
        result = read({"DEBUG": "False"}, argv=["manage.py", "test", "src", "-t", "src"])

        self.assertEqual(result["SECRET_KEY"], DEV_SECRET_KEY)

    def test_values_are_read_from_the_env_file_and_the_environment_wins(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / ".env"
            env_file.write_text(
                "SECRET_KEY=from-file\nDEBUG=True\nALLOWED_HOSTS=file.example.com\n"
            )

            result = read({"SECRET_KEY": "from-env"}, env_file=env_file)

        self.assertEqual(result["SECRET_KEY"], "from-env")
        self.assertNotIn("ALLOWED_HOSTS", os.environ)
        self.assertIs(result["DEBUG"], True)
        self.assertEqual(result["ALLOWED_HOSTS"], ["file.example.com"])
