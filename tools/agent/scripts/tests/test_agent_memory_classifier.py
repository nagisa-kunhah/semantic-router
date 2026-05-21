import importlib
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

classifier = importlib.import_module("agent_memory_classifier")


class AgentMemoryClassifierTests(unittest.TestCase):
    def classify(self, *, body="", additions=250, deletions=250, changed_files=None):
        with tempfile.TemporaryDirectory() as temp_dir:
            return classifier.classify_pr(
                body=body,
                additions=additions,
                deletions=deletions,
                changed_files=changed_files or [],
                repo_root=Path(temp_dir),
            )

    def test_large_pr_without_brief_is_missing(self) -> None:
        result = self.classify(additions=400, deletions=101)

        self.assertTrue(result.memory_required)
        self.assertFalse(result.memory_present)
        self.assertEqual(result.labels_to_add, ["agent-memory-missing"])

    def test_large_pr_with_valid_changed_brief_is_present(self) -> None:
        path = "docs/agent/reviews/2026/2026-05-21-router-review-brief.md"
        result = self.classify(
            body=f"Review brief: {path}",
            changed_files=[path],
        )

        self.assertTrue(result.memory_required)
        self.assertTrue(result.memory_present)
        self.assertEqual(result.memory_path, path)
        self.assertEqual(result.labels_to_add, ["agent-memory-present"])

    def test_small_pr_without_brief_is_not_required(self) -> None:
        result = self.classify(additions=10, deletions=20)

        self.assertFalse(result.memory_required)
        self.assertFalse(result.memory_invalid)
        self.assertEqual(result.labels_to_add, ["agent-memory-not-required"])

    def test_invalid_brief_path_is_invalid(self) -> None:
        result = self.classify(body="Review brief: docs/agent/reviews/nope.md")

        self.assertTrue(result.memory_invalid)
        self.assertIn("must match", result.invalid_reason or "")
        self.assertEqual(result.labels_to_add, ["agent-memory-missing"])

    def test_brief_outside_review_directory_is_invalid(self) -> None:
        result = self.classify(body="Review brief: memory.md")

        self.assertTrue(result.memory_invalid)
        self.assertIn("docs/agent/reviews", result.invalid_reason or "")

    def test_existing_base_branch_brief_is_present(self) -> None:
        path = "docs/agent/reviews/2026/2026-05-21-existing-brief.md"
        with tempfile.TemporaryDirectory() as temp_dir:
            brief_path = Path(temp_dir) / path
            brief_path.parent.mkdir(parents=True)
            brief_path.write_text("# Review Brief\n", encoding="utf-8")

            result = classifier.classify_pr(
                body=f"Review brief: {path}",
                additions=500,
                deletions=0,
                changed_files=[],
                repo_root=Path(temp_dir),
            )

        self.assertTrue(result.memory_present)
        self.assertEqual(result.labels_to_add, ["agent-memory-present"])


if __name__ == "__main__":
    unittest.main()
