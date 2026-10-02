from pathlib import Path

import yaml
from django.conf import settings
from django.test import SimpleTestCase

from config.env import DEV_SECRET_KEY

WORKFLOW_PATH = Path(settings.BASE_DIR).parent / ".github" / "workflows" / "ci.yml"


def load_workflow():
    return yaml.safe_load(WORKFLOW_PATH.read_text())


def step_actions(steps):
    """The action each step uses, without its version (`""` for run steps)."""
    return [step.get("uses", "").split("@")[0] for step in steps]


def step_commands(steps):
    """The shell command each step runs (`""` for action steps)."""
    return [step.get("run", "").strip() for step in steps]


class CiWorkflowTests(SimpleTestCase):
    def test_defines_a_single_test_job_without_matrix(self):
        self.assertTrue(WORKFLOW_PATH.exists(), f"{WORKFLOW_PATH} is missing")
        jobs = load_workflow()["jobs"]

        self.assertEqual(list(jobs), ["test"])
        self.assertNotIn("matrix", jobs["test"].get("strategy", {}))

    def test_triggers_on_every_push_and_on_prs_into_develop_and_main(self):
        workflow = load_workflow()
        # PyYAML follows YAML 1.1, where the bare key `on` loads as True.
        triggers = workflow.get("on", workflow.get(True))

        self.assertIsInstance(triggers, dict)
        self.assertIn("push", triggers)
        self.assertNotIn("branches", triggers["push"] or {})
        self.assertEqual(sorted(triggers["pull_request"]["branches"]), ["develop", "main"])

    def test_runs_on_ubuntu_with_checkout_and_cached_python_3_14(self):
        job = load_workflow()["jobs"]["test"]
        actions = step_actions(job["steps"])

        self.assertEqual(job["runs-on"], "ubuntu-latest")
        self.assertIn("actions/checkout", actions)
        self.assertIn("actions/setup-python", actions)
        setup_python = job["steps"][actions.index("actions/setup-python")]
        self.assertEqual(
            setup_python["with"],
            {
                "python-version": "3.14",
                "cache": "pip",
                "cache-dependency-path": "requirements.txt",
            },
        )

    def test_installs_requirements_after_setting_up_python(self):
        steps = load_workflow()["jobs"]["test"]["steps"]
        actions = step_actions(steps)
        commands = step_commands(steps)

        self.assertIn("pip install -r requirements.txt", commands)
        self.assertGreater(
            commands.index("pip install -r requirements.txt"),
            actions.index("actions/setup-python"),
        )

    def test_runs_system_checks_then_the_test_suite_after_installing(self):
        job = load_workflow()["jobs"]["test"]
        commands = step_commands(job["steps"])
        install = commands.index("pip install -r requirements.txt")

        self.assertEqual(
            commands[install + 1 :],
            ["python src/manage.py check", "python src/manage.py test src -t src"],
        )
        self.assertNotIn("continue-on-error", job)
        for step in job["steps"]:
            self.assertNotIn("continue-on-error", step)

    def test_sets_a_non_secret_ci_secret_key_for_the_job(self):
        job = load_workflow()["jobs"]["test"]
        secret_key = job.get("env", {}).get("SECRET_KEY", "")

        self.assertTrue(secret_key, "the test job sets no SECRET_KEY")
        self.assertNotEqual(secret_key, DEV_SECRET_KEY)
