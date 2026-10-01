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
