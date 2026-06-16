import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TEST_PATH_RE = re.compile(r"`(backend/tests/[^`]+\.py)`")


def test_browser_evidence_references_existing_test_files() -> None:
    evidence = (REPO_ROOT / "docs" / "browser-evidence.md").read_text(encoding="utf-8")

    referenced_tests = TEST_PATH_RE.findall(evidence)

    assert referenced_tests
    assert all((REPO_ROOT / test_path).exists() for test_path in referenced_tests)
