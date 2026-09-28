---
name: agents-never-merge-or-deploy
description: Agents never stage, commit, push or merge without an explicit go for that specific action. Merging to main is deploying.
type: feedback
---

Agents make and verify changes in the working tree, then stop and ask. Each stage, commit and push needs
its own explicit approval; approval for one doesn't carry over to the next. Merging a PR is always mine.
It isn't implied by "do everything", and it isn't implied by green CI.

**Why:** a push to `main` runs the deploy workflow straight to production. An agent once committed a
wording change on what it believed was a feature branch; it was `main`, and the change reached production
without a PR. It was harmless that time; the process wasn't. Another agent merged two PRs because CI was
green and the instruction had been "do everything that's not a big deal".

**How to apply:**
- Run `git branch --show-current` before any commit. On `main` or `develop`, stop and branch.
- An agent's ceiling: push the approved branch, open the PR, watch CI, report. Then stop.
