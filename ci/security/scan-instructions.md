# Custom security scan instructions — dom-backend

These instructions are appended to Claude's security-audit prompt. This is a
multi-tenant NestJS + Prisma backend, so tenant data isolation is the top
priority alongside the usual web vulnerability classes.

## Multi-tenant data isolation (HIGHEST PRIORITY)

Every tenant's data must stay isolated. Treat the following as HIGH or
CRITICAL findings:

- A Prisma query against a tenant-scoped model (`findMany`, `findFirst`,
  `findUnique`, `update`, `updateMany`, `upsert`, `delete`, `deleteMany`,
  `count`, `aggregate`, `groupBy`) whose `where` clause does NOT constrain a
  tenant key (e.g. `tenantId`, `organizationId`, `companyId`, `accountId`).
- A tenant identifier read from request input (route params, query string,
  request body, or a client-supplied header) instead of from the
  authenticated session / JWT / auth context. Tenant scoping derived from
  user-controlled input is a tenant-isolation bypass.
- `prisma.$queryRaw`, `$queryRawUnsafe`, `$executeRaw`, `$executeRawUnsafe`
  built with string interpolation of tenant or user input.
- Code that bypasses the shared tenant-scoped Prisma client / repository /
  middleware extension and calls the base `prisma` client directly for a
  tenant-scoped model.
- A `findUnique` / `findFirst` by global primary key that returns a
  tenant-scoped record without a subsequent tenant-ownership check.
- Mass assignment (`data: { ...body }`) that could let a caller set or
  overwrite `tenantId` / `organizationId`.

For each finding, give the file and line, explain why it breaks tenant
isolation, describe the concrete exploit (how one tenant could read or write
another tenant's data), and propose the minimal fix (derive and apply the
tenant filter from the auth context).

## Other priorities for this codebase

- AuthN / AuthZ: missing guards on controllers or resolvers, broken role
  checks, and IDOR (insecure direct object reference).
- Injection: SQL / NoSQL / command injection, especially raw Prisma queries.
- Secrets: hardcoded credentials, tokens, or keys; secrets written to logs.
  Slow-query logging must not log sensitive field values.
- Sensitive data exposure in API responses: over-fetching or returning full
  user/tenant records including PII or password hashes.
