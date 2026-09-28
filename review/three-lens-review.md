# Three-lens review

Runs before any user-facing PR opens, on the applied tree: the code as it will merge, not a plan.

A single correctness pass misses what matters most in this product: parity between the web app and the
phone app, readability for older care staff on cheap phones, help text, and compatibility with app
versions still in the field. So three read-only reviewer agents run in parallel, one lens each.

| Lens | Looks for |
|---|---|
| **1. UX, parity, design** | Web/phone parity, readability, copy in every supported language, empty and error states, the flow on a low-end Android phone |
| **2. Code quality and tests** | Correctness, simpler shapes, dead code, missing or weak tests |
| **3. Compatibility, security, docs** | Old app versions still sending traffic, API contract changes, tenant isolation, auth, help articles and docs |

## Rules

- Every finding comes with `file:line` and a concrete failure scenario. No scenario, no finding.
- Findings are claims, not verdicts. Each one is checked against the code before it is applied;
  reviewers are confidently wrong often enough.
- After the fixes, one more targeted pass over only what the fixes changed. Fixes introduce bugs too.
- The report says which review ran. "Correctness pass" and "three-lens review" are different claims.
- After merge, one more pass over what actually merged. Anything found becomes a follow-up PR in the
  same session.

## Why

In September 2026 a correctness review passed a batch of user-facing PRs. This review then found three
real problems in them, one of them a compatibility check that could have passed while phones in the
field were still sending the old field.
