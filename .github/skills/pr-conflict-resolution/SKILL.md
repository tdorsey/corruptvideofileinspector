---
name: pr-conflict-resolution
description: Skill for resolving pull request merge conflicts in the Corrupt Video File Inspector project
---

# PR Conflict Resolution Skill

This skill focuses on resolving merge conflicts in pull requests and restoring
mergeability without introducing new features or unrelated changes.

## When to Use

- A pull request is not mergeable (`mergeable == false` or `dirty`).
- The PR has the `status:merge-conflict` label applied.
- The goal is to resolve conflicts, not to add new functionality.

## Core Responsibilities

1. Resolve merge conflicts with minimal, targeted changes.
2. Ensure no conflict markers remain in the codebase.
3. Preserve the intended behavior from both branches.
4. Validate that required checks pass when available.

## Boundaries and Tool Usage

- Do not implement new features, enhancements, or refactors.
- Avoid unrelated formatting or cleanup changes.
- Do not update dependencies unless required to resolve the conflict.
- Use existing tools (`make check`, `make test`) instead of adding new scripts.
- Avoid destructive git operations (force push, rebase) unless explicitly required.

## Definition of Done

- No conflicted files remain in the working tree.
- No test failures are introduced (`make check` and `make test` succeed).
- No workflow runs are failing after conflict resolution.
- The pull request is mergeable and ready for review.

## Recommended Steps

1. Identify conflicting files and understand intent from each branch.
2. Resolve conflicts with the smallest possible edits.
3. Re-run checks to confirm a clean resolution.
