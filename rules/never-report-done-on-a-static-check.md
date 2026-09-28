---
name: never-report-done-on-a-static-check
description: For UI work, a green typecheck and build prove the code compiles, not that it works. Run it, then say exactly what was and wasn't verified.
type: feedback
---

Don't report UI work as done on `tsc` + `vite build` alone. Static checks prove the code compiles and
links. They don't prove that tabs render, routes resolve, redirects fire or data arrives.

**Why:** a tabs refactor was reported complete after only a typecheck and a build, which can't catch
broken sticky positioning, redirects that never fire or missing data wiring.

**How to apply:**
- Start the dev server and watch it for compile errors, route-generation failures and runtime warnings.
- Exercise the change in a browser or an emulator.
- In the report, separate what ran from what only compiled. "Dev server up, no errors; click flows not
  verified" is a good report. Silence is not.
- Enforced by [`hooks/prove-it-stop.sh`](../hooks/prove-it-stop.sh).
