import importlib
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

review_context = importlib.import_module("agent_review_context")


class AgentReviewContextTests(unittest.TestCase):
    def build_prompt(self, repo_root: Path, *, body="", classifier_data=None):
        metadata = {
            "number": 12,
            "title": "Router update",
            "body": body,
            "additions": 600,
            "deletions": 10,
            "changed_files": ["src/semantic-router/pkg/example.go"],
        }
        inputs = review_context.ContextInputs(
            metadata=metadata,
            classifier=classifier_data or {},
            diff="diff --git a/src/semantic-router/pkg/example.go b/src/semantic-router/pkg/example.go\n",
            repo_root=repo_root,
        )
        return review_context.build_review_prompt(inputs, max_historical_briefs=3)

    def test_current_brief_is_marked_author_provided(self) -> None:
        path = "docs/agent/reviews/2026/2026-05-21-router-brief.md"
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            brief_path = root / path
            brief_path.parent.mkdir(parents=True)
            brief_path.write_text("# Review Brief\n\nNot verified: tests.\n", encoding="utf-8")

            prompt = self.build_prompt(
                root,
                body=f"Review brief: {path}",
                classifier_data={"memory_path": path, "memory_present": True},
            )

        self.assertIn("## Author-provided review brief", prompt)
        self.assertIn("Not verified: tests.", prompt)
        self.assertIn("Brief / Diff Consistency", prompt)
        self.assertIn("trust the diff", prompt)

    def test_historical_briefs_are_module_related_and_limited(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            review_dir = root / "docs/agent/reviews/2026"
            review_dir.mkdir(parents=True)
            for index in range(5):
                (review_dir / f"2026-05-2{index}-router-{index}.md").write_text(
                    "# Review Brief\n\nRouter historical context.\n",
                    encoding="utf-8",
                )
            (review_dir / "2026-05-30-dashboard.md").write_text(
                "# Review Brief\n\nDashboard only.\n",
                encoding="utf-8",
            )

            prompt = self.build_prompt(root)

        self.assertEqual(prompt.count("## Historical review brief, possibly stale"), 3)
        self.assertIn("router-", prompt)
        self.assertNotIn("Dashboard only.", prompt)

    def test_missing_memory_still_builds_limited_review_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            prompt = self.build_prompt(Path(temp_dir))

        self.assertIn("- Memory context: missing", prompt)
        self.assertIn("## PR Diff", prompt)
        self.assertIn("## Findings", prompt)


if __name__ == "__main__":
    unittest.main()
