from pathlib import Path

import yaml
from django.conf import settings
from django.test import SimpleTestCase

WORKFLOW_PATH = Path(settings.BASE_DIR).parent / ".github" / "workflows" / "ci.yml"


def load_workflow():
    return yaml.safe_load(WORKFLOW_PATH.read_text())


class CiWorkflowTests(SimpleTestCase):
    def test_defines_a_single_test_job_without_matrix(self):
        self.assertTrue(WORKFLOW_PATH.exists(), f"{WORKFLOW_PATH} is missing")
        jobs = load_workflow()["jobs"]

        self.assertEqual(list(jobs), ["test"])
        self.assertNotIn("matrix", jobs["test"].get("strategy", {}))
