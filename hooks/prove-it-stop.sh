#!/bin/sh
# Claude Code Stop hook. If the agent changed UI files in the last 10 minutes, block the stop once
# and make it say what it actually verified at runtime, as opposed to what only compiled.
input=$(cat)
sid=$(echo "$input" | jq -r '.session_id // "noid"')
marker="/tmp/.claude-ui-verify-${sid}"
[ -f "$marker" ] && exit 0
root="${CLAUDE_PROJECT_DIR:-$PWD}"
recent=$(find "$root" -path '*/node_modules' -prune -o -path '*/dist' -prune -o -path '*/.git' -prune -o \
  -type f \( -name '*.tsx' -o -name '*.jsx' \) -mmin -10 -print 2>/dev/null | head -1)
[ -z "$recent" ] && exit 0
touch "$marker"
printf '%s' '{"decision":"block","reason":"UI files were modified in the last 10 minutes. Before stopping: (1) did you start `npm run dev` and check for compile/runtime errors? (2) if visual or interaction testing was not performed (no browser tool surfaced in this environment), say so explicitly — do not imply tests passed when only static checks (tsc, vite build) ran. State what was actually verified, then stop again."}'
