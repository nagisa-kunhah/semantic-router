# Review Briefs

Review briefs are author-provided context for large or risky pull requests. They help reviewers and review automation understand the intended shape of a change without treating chat history, local notes, or generated memory files as authoritative.

Review briefs are not raw `memory.md` files. They should be short, durable Markdown files committed under:

```text
docs/agent/reviews/YYYY/YYYY-MM-DD-<short-kebab-title>.md
```

Use this exact template:

```md
# Review Brief

## Summary

## Changed Areas

## Key Decisions

## Validation

## Reviewer Focus

## Risks or Follow-ups
```

## Authoring Rules

- The brief may be drafted by AI, but the PR author must confirm that it matches the code, PR body, changed files, and available validation evidence.
- The brief is an **Author-provided review brief**. It is context for reviewers, not a source of truth.
- Reviewers and bots must prefer the PR diff, changed files, PR body, and actual test output when they conflict with the brief.
- Any claim that cannot be confirmed from the diff, changed files, PR body, or test output must be marked `Not verified` or `Author stated`.
- Do not include secrets, credentials, private data, raw logs, or chain-of-thought.
- Do not describe planned work as completed work. Put incomplete work in `Risks or Follow-ups`.

## Rollout

The initial rollout labels PRs so maintainers can observe how review briefs affect AI-assisted review quality. Missing briefs should produce labels and comments, not a hard CI failure, until the repository explicitly promotes the check to a gate.
