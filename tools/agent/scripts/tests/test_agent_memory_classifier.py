import importlib
import re
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

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

    def test_workflow_creates_labels_and_removes_only_current_agent_labels(
        self,
    ) -> None:
        workflow_path = (
            SCRIPT_DIR.parents[2] / ".github/workflows/agent-memory-classifier.yml"
        )
        workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
        update_step = next(
            step
            for step in workflow["jobs"]["classify"]["steps"]
            if step.get("name") == "Update memory labels"
        )
        script = update_step["with"]["script"]

        for label in classifier.LABELS:
            self.assertIn(f"'{label}'", script)
        self.assertIn("github.rest.issues.createLabel", script)
        self.assertIn("github.rest.issues.listLabelsOnIssue", script)
        self.assertIn("currentLabelNames.has(name)", script)
        self.assertNotRegex(
            script,
            re.compile(
                r"for \(const name of labelsToRemove\).*?try\s*{.*?removeLabel",
                re.DOTALL,
            ),
        )

    def test_workflows_request_pr_write_for_pr_label_and_comment_apis(self) -> None:
        workflow_paths = (
            SCRIPT_DIR.parents[2] / ".github/workflows/agent-memory-classifier.yml",
            SCRIPT_DIR.parents[2] / ".github/workflows/agent-memory-review.yml",
        )
        for workflow_path in workflow_paths:
            with self.subTest(workflow=workflow_path.name):
                workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
                self.assertEqual(workflow["permissions"]["issues"], "write")
                self.assertEqual(workflow["permissions"]["pull-requests"], "write")


if __name__ == "__main__":
    unittest.main()
