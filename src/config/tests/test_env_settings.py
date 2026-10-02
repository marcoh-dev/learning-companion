import importlib.util
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

REPO_ROOT = Path(settings.BASE_DIR).parent
REQUIREMENTS_PATH = REPO_ROOT / "requirements.txt"


class RequirementsTests(SimpleTestCase):
    def test_django_environ_is_pinned_and_importable(self):
        lines = REQUIREMENTS_PATH.read_text().splitlines()

        self.assertIn("django-environ==0.14.0", lines)
        self.assertIsNotNone(importlib.util.find_spec("environ"))
