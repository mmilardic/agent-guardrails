---
name: land-or-park-before-starting-new
description: Before starting a new thread, land or explicitly park what is already at 95%. Every session ends by naming the one step left.
type: feedback
---

Unfinished work doesn't show up in throughput numbers. Before opening anything new, list what is built
but uncommitted, open but unmerged, and merged but unreleased. Land it, or park it on purpose with the
single remaining step written down.

**Why:** on 4 September 2026 a count found nine threads sitting at 95% (uncommitted branches, PRs
waiting for a device retest, a backend and web pair waiting to deploy together) while PR throughput
looked great.

**How to apply:** when a new thread starts, say whether it adds to the pile. When a session ends with
something unfinished, name the one remaining step, and put parked work first in the next session's report.
