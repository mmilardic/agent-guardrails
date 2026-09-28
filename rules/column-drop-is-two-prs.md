---
name: column-drop-is-two-prs
description: Dropping a database column takes two PRs. Stop using it first; drop it once no deployed code reads it.
type: feedback
---

PR 1 removes every read and write and keeps the Prisma field marked `@ignore`: the column stays in the
datamodel, so there is no schema drift, but the generated client can't touch it. PR 2, once PR 1 is in
production, holds the `DROP COLUMN` migration and removes the field.

**Why:** a rollback restores the code, never the schema. If one PR removes the field and drops the
column, rolling it back ships code that reads a column that no longer exists. Removing the field
outright in PR 1 also leaves the schema and the migration history disagreeing, and the next
`migrate dev` folds the drop into an unrelated migration.

**How to apply:** rehearse the drop on a production-copy database through `migrate deploy`, run the app
and the test suites against the column-less table, then restore that database. Nothing is run by hand on
production; every step is a merge.
