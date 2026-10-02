import importlib
import importlib.util
import os
import sys
import tempfile
import warnings
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from config import settings as config_settings
from config.env import DEV_SECRET_KEY, read_settings

REPO_ROOT = Path(settings.BASE_DIR).parent
REQUIREMENTS_PATH = REPO_ROOT / "requirements.txt"
ENV_EXAMPLE_PATH = REPO_ROOT / ".env.example"


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
                "ENV_SETTINGS_TEST_ONLY=from-file\n"
            )

            # patch.dict restores os.environ even if a regression writes to it.
            with mock.patch.dict(os.environ):
                environ_before = dict(os.environ)
                result = read({"SECRET_KEY": "from-env"}, env_file=env_file)
                environ_after = dict(os.environ)

        self.assertEqual(environ_after, environ_before)
        self.assertEqual(result["SECRET_KEY"], "from-env")
        self.assertIs(result["DEBUG"], True)
        self.assertEqual(result["ALLOWED_HOSTS"], ["file.example.com"])

    def test_missing_env_file_loads_defaults_without_warnings_or_log_messages(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            with self.assertNoLogs(level="INFO"):
                result = read({"DEBUG": "True"}, env_file=MISSING_ENV_FILE)

        self.assertEqual(result["SECRET_KEY"], DEV_SECRET_KEY)
        self.assertEqual(result["ALLOWED_HOSTS"], ["localhost", "127.0.0.1"])

    def test_secret_key_starting_with_dollar_is_taken_verbatim(self):
        # django-environ would otherwise resolve `$name` as a reference to another variable.
        result = read({"SECRET_KEY": "$abc123", "abc123": "other", "DEBUG": "False"})

        self.assertEqual(result["SECRET_KEY"], "$abc123")

    def test_placeholder_secret_key_with_debug_off_is_improperly_configured(self):
        for placeholder in ["change-me", "django-insecure-anything", DEV_SECRET_KEY]:
            with self.subTest(SECRET_KEY=placeholder):
                with self.assertRaisesMessage(ImproperlyConfigured, "SECRET_KEY"):
                    read({"SECRET_KEY": placeholder, "DEBUG": "False"})

    def test_test_command_replaces_a_placeholder_secret_key_with_the_dev_key(self):
        result = read({"SECRET_KEY": "change-me", "DEBUG": "False"}, argv=["manage.py", "test"])

        self.assertEqual(result["SECRET_KEY"], DEV_SECRET_KEY)


class SettingsWiringTests(SimpleTestCase):
    def test_settings_take_their_values_from_read_settings(self):
        values = {"SECRET_KEY": "patched", "DEBUG": True, "ALLOWED_HOSTS": ["patched.example"]}
        self.addCleanup(importlib.reload, config_settings)

        with mock.patch("config.env.read_settings", return_value=values) as read_mock:
            module = importlib.reload(config_settings)

        read_mock.assert_called_once_with(os.environ, REPO_ROOT / ".env", sys.argv)
        self.assertEqual(module.SECRET_KEY, "patched")
        self.assertIs(module.DEBUG, True)
        self.assertEqual(module.ALLOWED_HOSTS, ["patched.example"])

    def test_the_old_hardcoded_secret_key_is_gone_from_src(self):
        # Assembled at runtime so this file doesn't contain the old key either.
        old_key_fragment = "django-insecure-" + "4$t-4q$zq9"
        sources = Path(settings.BASE_DIR).rglob("*.py")

        offenders = [str(path) for path in sources if old_key_fragment in path.read_text()]

        self.assertEqual(offenders, [])


class EnvExampleTests(SimpleTestCase):
    def test_documents_every_variable_with_an_example_value_and_a_comment(self):
        lines = ENV_EXAMPLE_PATH.read_text().splitlines()
        expected = [
            "SECRET_KEY=change-me",
            "DEBUG=True",
            "ALLOWED_HOSTS=localhost,127.0.0.1",
            "OPENAI_API_KEY=",
            "OPENAI_MODEL=",
        ]

        assignments = [line for line in lines if line and not line.startswith("#")]
        self.assertEqual(assignments, expected)
        for assignment in expected:
            with self.subTest(assignment=assignment):
                previous = lines[lines.index(assignment) - 1]
                self.assertTrue(previous.startswith("# "), f"no comment above {assignment}")

    def test_env_file_is_git_ignored(self):
        ignored = (REPO_ROOT / ".gitignore").read_text().splitlines()

        self.assertIn(".env", ignored)


class SetupDocsTests(SimpleTestCase):
    def test_setup_instructions_mention_copying_env_example(self):
        for doc in ["CLAUDE.md", "README.md"]:
            with self.subTest(doc=doc):
                self.assertIn("cp .env.example .env", (REPO_ROOT / doc).read_text())
