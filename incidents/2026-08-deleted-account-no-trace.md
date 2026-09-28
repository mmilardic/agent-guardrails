# Incident review: a deleted account with no trace in the logs

August 2026 · blameless · Marko Milardić

## Summary

A staff account at one of the care homes using DomPlus disappeared. The database showed what had
happened: the employee record was soft-deleted and the account row hard-deleted in the same transaction.
Nothing showed who did it. The request had succeeded normally, but the access log hadn't kept it: it
sampled away 95% of fast successful requests, so a successful DELETE was treated like a dashboard poll.
The sampling rule was fixed the same day, and the investigation became a review of the whole logging and
metrics path. Five PRs were in production within three days.

## Impact

- One staff account at one care home was deleted.
- We could not identify who deleted it. In a system that holds residents' care records, "who changed
  this?" is a question we have to be able to answer.

## Timeline

| When | What |
|---|---|
| August | A staff account at one home is found missing. Grafana has no log line for it. |
| 17 Aug | Database forensics reconstruct what happened (two rows changed with an identical transaction timestamp), but not who. The root cause is found in the access-log middleware and the fix is merged the same day. |
| 17–20 Aug | A review of the whole logging and metrics path finds more latent problems, fixed in four more PRs. |
| 20 Aug | All five PRs are in production. |

## Root cause

Access logging sampled 95% of fast 2xx responses to keep volume down. Most traffic is reads, because
tables refetch every 10 seconds, but the sampler didn't tell reads from writes. The DELETE had a 5%
chance of being logged and lost the roll. The only trace left was a request-counter increment, which
carries no account ID.

Contributing factors:

- The logging docs said the request line fires on "every request" and qualified it only a sentence
  later. That wording set the wrong expectation.
- Logs and metrics are recorded at different moments (connection close vs. response finish) and only
  the logs are sampled, so the two never reconcile. A missing event looked like a normal gap.

## What changed

1. **Writes are never sampled.** POST, PUT, PATCH and DELETE bypass the sampler; reads still sample at
   5%. Every write line carries the account, tenant, request ID, IP and user agent, so a repeat names
   the actor. Cost: about 3–5k writes a day, 60–75 MB a month. A test asserts that reads are still
   sampled, so the bypass can't quietly widen.
2. **Every error and warning is a named event.** The structured logger accepts only names from one typed
   list, so an ad-hoc name is a compile error, and a test fails the build if the list and the docs
   disagree. Alerts match event names, not substrings.
3. **One line per error, with the cause attached.** Wrapped errors keep the original as `cause`, so the
   real failure's stack survives instead of the wrapper's.
4. **Log levels by audience.** 19 info lines that narrated requests moved to debug, which never leaves
   the machine. The warnings became four typed events, including one that fires when the
   tenant-isolation guard rejects a lookup.
5. **Metrics that survive scaling.** Pushed series now carry a process identity (two instances would
   otherwise corrupt each other's counters), a hand-rolled parser that a single space in a label value
   would have broken was replaced, and debug heartbeat lines stopped shipping to production.
6. **The docs say why logs and metrics differ,** and which to trust for what: logs for what happened to
   one request, metrics for how often something happens.

## What went well

- Database forensics established what happened even though the logs couldn't.
- The core fix was small (61 lines) and merged the same day. The wider review fixed problems before they
  caused incidents of their own.

## What didn't

- We found the gap through a real incident, not through a test or a review.
- The gap came from a sentence in the docs that promised more than the code did.

## Follow-ups

| Follow-up | Status |
|---|---|
| An audit trail that outlives log retention | Open |
| A safeguard in the account-delete flow | Open |
| Two alert rules adjusted for the new log events | Open |

## Lesson

Every sampling decision makes some question unanswerable. Write down which one, and never sample the
requests that change data.
