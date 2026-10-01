import json
import re
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

SCRIPT_PATH = Path(settings.BASE_DIR).parent / ".claude" / "scripts" / "protect-branches.sh"

# A `gh api ... branches/<branch>/protection ... <<'JSON'` call followed by its heredoc body.
PROTECTION_CALL = re.compile(
    r"branches/(?P<branch>[\w-]+)/protection[^\n]*<<'JSON'\n(?P<body>.*?)\nJSON\n",
    re.DOTALL,
)


def load_protection():
    """The protection payload `protect-branches.sh` sends for each branch."""
    script = SCRIPT_PATH.read_text()
    return {
        match["branch"]: json.loads(match["body"])
        for match in PROTECTION_CALL.finditer(script)
    }


class BranchProtectionTests(SimpleTestCase):
    def test_main_requires_source_branch_and_test_checks(self):
        main = load_protection()["main"]

        self.assertEqual(
            sorted(main["required_status_checks"]["contexts"]), ["source-branch", "test"]
        )
        self.assertTrue(main["enforce_admins"])
        self.assertFalse(main["allow_force_pushes"])
        self.assertFalse(main["allow_deletions"])

    def test_develop_requires_test_check_but_lets_admins_push_the_main_sync(self):
        develop = load_protection()["develop"]

        self.assertEqual(
            develop["required_status_checks"], {"strict": False, "contexts": ["test"]}
        )
        self.assertFalse(develop["enforce_admins"])
        self.assertIsNone(develop["required_pull_request_reviews"])
        self.assertFalse(develop["allow_force_pushes"])
        self.assertFalse(develop["allow_deletions"])
