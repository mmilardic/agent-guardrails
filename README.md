# agent-guardrails

How I run engineering for [DomPlus](https://domplus.app), software for care homes in Croatia and Bosnia
and Herzegovina, as one person working with AI coding agents in parallel: the guardrails, review gates,
CI and written rules that keep it fast without letting it get sloppy.

These are cleaned-up copies of the real files from private repos. Local paths are generalised and
product details removed; the logic is unchanged.

For scale: my own merged PRs across the three code repos (backend, web, mobile) went from about 45 a
month in March–May 2026 to about 200 a month since July, full-time in both periods. PR count is a crude
number and I'd never judge a person by it. The point of everything here is holding quality at that pace.

## How work flows

1. **One queue, one written brief per task.** The queue has the priority order at the top and a
   parked-debt list where each item is scheduled or explicitly killed. Each task gets a
   [brief](process/brief-template.md), and agents work in separate git worktrees, so three or four
   workstreams run at once.
2. **Guardrails while an agent works.** [`permission-gate.py`](hooks/permission-gate.py) hard-blocks
   destructive commands even inside chained commands, auto-approves the normal toolchain and asks me
   about everything else, so agents run unattended with a small worst case.
   [`prove-it-stop.sh`](hooks/prove-it-stop.sh) stops an agent that changed UI files from finishing
   until it says what it ran in a browser or emulator, as opposed to what only compiled.
3. **Review before the PR.** [Three read-only reviewer agents](review/three-lens-review.md), one lens
   each, then a second pass on whatever the fixes changed. My review is the last step, not the whole job.
4. **CI.** A [Claude security review on every PR](ci/security-review-pr.yml) with
   [tenant-isolation scan instructions](ci/security/scan-instructions.md), and a
   [monthly full-repo audit](ci/security-scheduled.yml) that opens one issue or stays silent.
   [Tests run on PRs only](ci/tests.yml) and [deploys never wait on them](ci/heroku-deploy.yml); the
   comments in both files say why.
5. **The merge is mine.** Agents never merge or deploy.
6. **Written memory.** Every correction becomes a rule with its reason, and every agent session starts
   from those rules. [Six examples](rules/).

## Where I don't trust agents yet

- **Their own "it works".** Hence the prove-it hook, the review lenses and runtime checks.
- **Factual or legal claims without a primary source.** See [the rule](rules/claims-need-a-primary-source.md).
- **Anything irreversible.** See [the rule](rules/agents-never-merge-or-deploy.md).

## Incident review

[A deleted account with no trace in the logs](incidents/2026-08-deleted-account-no-trace.md): a blameless
write-up of a production incident, its root cause (log sampling) and the five PRs that changed how the
backend logs.

## Layout

    hooks/                  permission-gate.py, prove-it-stop.sh
    settings.example.json   how the hooks are wired into Claude Code
    ci/                     GitHub Actions workflows (kept out of .github/ here so they don't run)
    review/                 the three-lens review
    process/                the brief template
    rules/                  six of the written rules
    incidents/              incident reviews

In my setup the stop hook is an inline command in the Claude Code settings; here it's a script so it's
readable.

Marko Milardić · founder of DomPlus · previously engineer at Rimac, Infobip and EveryMatrix
