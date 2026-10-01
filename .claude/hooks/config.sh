# Project-specific configuration for the workflow hooks.
# Adapt these to your project. Everything else should work unchanged.

TEST_CMD=".venv/bin/python src/manage.py test src -t src"
LINT_CMD=".venv/bin/python src/manage.py check"

# File whose presence means "the project is set up, run the suite".
PROJECT_MARKER="src/manage.py"

# Run the test suite after every source/test file write (records red/green
# for the TDD cycle). Set to "false" if your suite is too slow for that;
# tests are then only enforced at commit time.
RUN_TESTS_ON_WRITE="true"

# Branches that may never receive direct commits or force-pushes. They only
# change through PRs (develop: squash-merged feature/fix PRs plus the
# main-sync merge commit; main: promotion PRs from develop).
PROTECTED_BRANCHES="main|master|develop"

# Directories that count as production/test code (used by the write guard).
SOURCE_DIRS="src"
