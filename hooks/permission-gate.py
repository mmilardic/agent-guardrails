#!/usr/bin/env python3
"""
Claude Code PreToolUse gate for Bash.
  - DENY  : dangerous patterns anywhere in the command (sudo, rm -rf /, etc.)
  - ALLOW : every top-level segment leads with a trusted command
  - else  : stay silent -> Claude Code shows its normal permission prompt
The denylist is checked against the RAW command, so it also catches
dangerous calls hidden inside && / | / $(...) chains.
Failure mode is always "fall through to a prompt", never a wrong approval.
"""
import sys, json, re

# Paths that count as "inside my work" and are therefore exempt from the
# rm-on-root / chown-on-root denials below.
_SAFE = r'Users/[^/]+/Projects|private/tmp|tmp(?:/|\b)'

DENY = [
    r'\bsudo\b',
    r'\bdoas\b',
    r'\brm\s+-[a-zA-Z]*\s+/(?!' + _SAFE + r')',   # rm -... /something outside my work
    r'\brm\s+-[a-zA-Z]*\s+~',
    r'\brm\s+-[a-zA-Z]*\s+\$HOME',
    r'\brm\s+(?:-[a-zA-Z]+\s+)*\*',               # rm -rf *  (wipe cwd)
    r'\brm\s+(?:-[a-zA-Z]+\s+)*\.\.?(?:\s|;|&|\||$)',  # rm -rf .  or  ..  (whole dir, but not ./path)
    r'\bmkfs\b',
    r'\bdd\s+if=',
    r':\s*\(\s*\)\s*\{',                           # fork bomb  :(){ ... }
    r'\bchmod\s+-R\s+777\s+/',
    r'\bchown\s+-R\b[^|;&]*\s+/(?!' + _SAFE + r')',
    r'>\s*/dev/(?:disk|sd|rdisk)',
    r'\bdiskutil\s+(?:erase|reformat|partitionDisk)',
    r'\b(?:curl|wget)\b[^|]*\|\s*(?:sudo\s+)?(?:ba)?sh\b',   # curl ... | sh
    r'>\s*/etc/',
    r'>\s*~/\.(?:bashrc|zshrc|profile|ssh)',
]

ALLOWED = {
    # node / js toolchain
    'npm','npx','node','yarn','pnpm','tsc','jest','vitest','eslint','prettier','vite','eas','expo',
    # python
    'python3','python','pip3','pip',
    # databases
    'psql','pg_ctl','pg_dump','pg_restore','initdb','prisma','redis-cli','mongosh','mysql',
    # git / github
    'git','gh',
    # network
    'curl','wget','ssh','scp','rsync',
    # containers
    'docker',
    # read / file utils
    'ls','cat','head','tail','grep','rg','find','sed','awk','jq','wc','stat','cd','echo','pwd',
    'touch','mkdir','rmdir','rm','cp','mv','xargs','sort','uniq','cut','tr','tee','diff','open','file',
    'lsof','ps','kill','pkill','pgrep','base64','mdls','qlmanage','sips','date','which','env','printf','true',
    # shell/util builtins commonly chained in scripts
    'seq','sleep','false','read','wait','dirname','basename','realpath','comm','nl','tac','rev',
    'column','du','df','type','command','hash','tput','shasum','md5','xxd','paste','expr','let','printenv',
    'set','unset','export','local','declare','pushd','popd','exit','perl','ruby',
    'claude','rg','fd','bat','tree','watch','time','nproc','sysctl','uname','whoami','id','groups',
    'ln','readlink','realpath','install','truncate','split','join','fold','seq','shuf','tsort',
    'source','.','chmod','chown','chgrp','chflags','ditto','rsync','tar','zip','unzip','gunzip','gzip',
    'nohup','nice','timeout','stdbuf','env',
    # mobile / simulator tooling
    'adb','xcrun','simctl','emulator','idb','applesimutils','fastlane','pod','gradlew','eas-cli',
    'hermes','hermesc','metro','watchman','xcodebuild','xcbeautify','ios-deploy','swift','swiftc',
    # shell interpreters (see caveat: these can run code the gate cannot inspect)
    'bash','sh','zsh',
    # macOS automation / UI scripting
    'osascript','cliclick','pbcopy','pbpaste','defaults','plutil','caffeinate','say','screencapture',
    'textutil','mdfind','hdiutil','codesign','spctl','xattr','diskutil','iconv','tidy',
    # pdf / image conversion tooling (brochure builds)
    'pdftoppm','pdftocairo','pdftotext','pdfinfo','pdfimages','pdfunite','pdfseparate',
    'qpdf','mutool','pdftk','gs','convert','magick','identify','mogrify','rsvg-convert',
}

def decision(kind, reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": kind,
        "permissionDecisionReason": reason,
    }}))

# keywords that PRECEDE a command (the next word is the command to check)
_PRECEDE = {'if','then','elif','else','while','until','do','!','time','coproc',
            'eval','command','exec','builtin','then;'}
# constructs whose following words are data/conditions, not commands to validate
_DATALEAD = {'for','select','case','[','[[','test'}
# terminators / list words that are never commands
_ENDERS = {'done','fi','esac','in','then;','{','}','break','continue','return',':'}

def _find_quote_end(s, i, q, end):
    i += 1
    while i < end and s[i] != q:
        i += 2 if s[i] == '\\' else 1
    return i + 1

def _find_paren_end(s, i, end):
    """i points just past '$(' or '('. Return index just past the matching ')'."""
    depth = 1
    while i < end and depth:
        c = s[i]
        if c in '"\'':
            i = _find_quote_end(s, i, c, end); continue
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
        i += 1
    return i

def _scan(s, i, end, expect, words, funcs, assigns):
    """Scan s[i:end] as a shell command sequence; append command basenames.
    `expect` is True when the next bare token would start a command.
    `funcs` collects shell function names so their definitions and calls
    aren't mistaken for external commands."""
    case_depth = 0
    in_pattern = False
    while i < end:
        c = s[i]
        if c in ' \t':
            i += 1; continue
        if c == '\\':
            i += 2; continue
        if c == ';' and i + 1 < end and s[i + 1] == ';':   # ';;' ends a case body
            if case_depth:
                in_pattern = True
            expect = True; i += 2; continue
        if c in ';\n|&{}':
            if c == '|' and in_pattern:     # 'a|b|c)' pattern alternation: data
                i += 1; continue
            expect = True; i += 1; continue
        if c == '(':
            if not expect:                 # bare parens in an argument, e.g. app/(main)/x.tsx
                i += 1; continue
            j = _find_paren_end(s, i + 1, end)
            _scan(s, i + 1, j - 1, True, words, funcs, assigns); i = j; expect = False; continue
        if c == ')':
            if in_pattern:                 # end of case pattern list -> body follows
                in_pattern = False; expect = True; i += 1; continue
            i += 1; continue               # stray close
        if c == '`':
            j = s.find('`', i + 1); j = end if j == -1 else j
            _scan(s, i + 1, j, True, words, funcs, assigns); i = j + 1; expect = False; continue
        if c == '$' and i + 1 < end and s[i + 1] == '(':
            if i + 2 < end and s[i + 2] == '(':     # $(( arithmetic )) — no commands inside
                j = _find_paren_end(s, i + 2, end); i = j; expect = False; continue
            j = _find_paren_end(s, i + 2, end)
            _scan(s, i + 2, j - 1, True, words, funcs, assigns); i = j; expect = False; continue
        if c in '<>':                      # redirection or process substitution <( ) >( )
            if i + 1 < end and s[i + 1] == '(':
                j = _find_paren_end(s, i + 2, end)
                _scan(s, i + 2, j - 1, True, words, funcs, assigns); i = j; expect = False; continue
            i += 1
            while i < end and s[i] in '&0123456789 \t':
                i += 1
            while i < end and s[i] not in ' \t;\n|&<>()`':
                i += 1
            continue
        if c == "'":
            i = _find_quote_end(s, i, "'", end); expect = False; continue
        if c == '"':                       # double quotes: recurse into $()/`` inside
            i += 1
            while i < end and s[i] != '"':
                if s[i] == '\\':
                    i += 2; continue
                if s[i] == '`':
                    j = s.find('`', i + 1); j = end if j == -1 else j
                    _scan(s, i + 1, j, True, words, funcs, assigns); i = j + 1; continue
                if s[i] == '$' and i + 1 < end and s[i + 1] == '(':
                    if i + 2 < end and s[i + 2] == '(':     # $(( arithmetic ))
                        j = _find_paren_end(s, i + 2, end); i = j; continue
                    j = _find_paren_end(s, i + 2, end)
                    _scan(s, i + 2, j - 1, True, words, funcs, assigns); i = j; continue
                i += 1
            i += 1; expect = False; continue
        if c == '#' and expect:            # shell comment: skip to end of line
            nl = s.find('\n', i)
            i = end if nl == -1 else nl
            continue
        # bare token (stop before an embedded $( so substitutions are handled)
        j = i
        while j < end and s[j] not in ' \t;\n|&<>()`"\'':
            if s[j] == '$' and j + 1 < end and s[j + 1] == '(':
                break
            j += 2 if s[j] == '\\' else 1
        token = s[i:j]; i = j
        if not expect:
            continue
        if re.match(r'^[A-Za-z_][A-Za-z0-9_]*(\[[^\]]*\])?\+?=', token):
            k = i
            while k < end and s[k] in ' \t':
                k += 1
            if k < end and s[k] == '(' and token.endswith('='):
                j = _find_paren_end(s, k + 1, end)   # array literal: data, skip it
                i = j; expect = False; continue
            # remember simple scalar assignments: VAR=value (value is the token's tail
            # plus the immediately-following bare word, if any) so a later $VAR command
            # can be resolved to its real basename.
            name = token.split('=', 1)[0]
            val = token.split('=', 1)[1]
            if not val and k < end and s[k] not in ' \t;\n|&<>()`"\'#':
                j2 = k
                while j2 < end and s[j2] not in ' \t;\n|&<>()`"\'':
                    j2 += 2 if s[j2] == '\\' else 1
                val = s[k:j2]; i = j2
            val = val.strip('"\'')
            if val and '$' not in val:
                assigns[name] = val.split('/')[-1]
            continue                       # VAR=val prefix; command still to come
        # function definition:  name ( )  { ... }
        k = i
        while k < end and s[k] in ' \t':
            k += 1
        if k + 1 < end and s[k] == '(' :
            k2 = k + 1
            while k2 < end and s[k2] in ' \t':
                k2 += 1
            if k2 < end and s[k2] == ')':
                funcs.add(token.split('/')[-1])
                i = k2 + 1; expect = True; continue   # body scanned via following {
        if token == 'case':
            case_depth += 1; in_pattern = True; expect = False; continue
        if token == 'esac':
            case_depth = max(0, case_depth - 1); in_pattern = False; expect = False; continue
        if in_pattern:
            continue                       # case pattern words are data, not commands
        if token in _DATALEAD or token in _ENDERS:
            expect = False; continue
        if token in _PRECEDE:
            continue                       # next token is the command
        base = token.split('/')[-1]
        m = re.fullmatch(r'\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?', base)
        if m and m.group(1) in assigns:
            base = assigns[m.group(1)]
        if base and not base.isdigit() and base not in funcs:
            words.append(base)
        expect = False
    return i

def command_words(cmd):
    """Basename of every command invoked anywhere in cmd, seeing through
    &&/||/|/;, subshells, $(...), backticks, nested quotes, redirects and loops."""
    s = re.sub(r'\\\n', ' ', cmd)          # join line-continuations
    words = []
    _scan(s, 0, len(s), True, words, set(), {})
    return words

INTERPRETERS = {'bash','sh','zsh','python3','python','node','perl','ruby','osascript','awk'}

def split_heredocs(cmd):
    """Return (cmd_without_bodies, code_bodies).
    Bodies that feed an interpreter (bash/python3/node...) are CODE and are
    returned for the deny scan. Bodies that are data (git commit -F -,
    cat > file) are dropped so message text isn't misread as commands."""
    lines = cmd.split('\n')
    out, code, i = [], [], 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        m = re.search(r"<<-?\s*[\"']?([A-Za-z_]\w*)[\"']?", line)
        i += 1
        if not m:
            continue
        delim = m.group(1)
        is_code = any(w.split('/')[-1] in INTERPRETERS for w in line.split())
        body = []
        while i < len(lines) and lines[i].strip().lstrip('\t') != delim:
            body.append(lines[i]); i += 1
        i += 1  # skip closing delimiter
        if is_code:
            code.extend(body)
    return '\n'.join(out), '\n'.join(code)

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    tool = data.get("tool_name")
    if tool in ("WebFetch", "WebSearch"):
        decision("allow", "Web access approved for research.")
        sys.exit(0)
    if tool != "Bash":
        sys.exit(0)
    raw = (data.get("tool_input", {}) or {}).get("command", "") or ""
    cmd, code_bodies = split_heredocs(raw)

    for p in DENY:
        if re.search(p, cmd) or (code_bodies and re.search(p, code_bodies)):
            decision("deny", "Blocked by local safety gate (dangerous pattern). Run it yourself if intended.")
            sys.exit(0)

    words = command_words(cmd)
    if words and all(w in ALLOWED for w in words):
        decision("allow", "All invoked commands are trusted.")
    sys.exit(0)

main()
