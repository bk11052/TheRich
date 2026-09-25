#!/usr/bin/env bash
# Pre-push audit: fail if secrets or personal data are tracked by git.
# Usage: ./scripts/audit-secrets.sh  (exit 0 = clean, 1 = findings)
set -uo pipefail
cd "$(dirname "$0")/.."
fail=0
note() { printf '\n== %s ==\n' "$1"; }
bad()  { printf '  [FAIL] %s\n' "$1"; fail=1; }
ok()   { printf '  [ok] %s\n' "$1"; }

SECRETS='(sk-ant-|sk-[A-Za-z0-9]{20,}|ghp_|gho_|github_pat_|AIza[0-9A-Za-z_-]{30,}|AKIA[0-9A-Z]{16}|xox[baprs]-|[0-9]{8,10}:AA[A-Za-z0-9_-]{30,})'
PII='(주민등록번호|[0-9]{6}-[1-4][0-9]{6}|01[016789]-?[0-9]{3,4}-?[0-9]{4}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})'
PATHS='(^|/)\.env$|\.db$|\.sqlite|^uploads/|혜택_청약'

note "1. Secret patterns in tracked files"
if git grep -nIE "$SECRETS" -- . ':!scripts/audit-secrets.sh'; then bad "secret-like string tracked"; else ok "none"; fi

note "2. PII patterns in tracked files"
if git grep -nIE "$PII" -- . ':!scripts/audit-secrets.sh'; then bad "PII-like string tracked"; else ok "none"; fi

note "3. Sensitive paths tracked"
if git ls-files | grep -aE "$PATHS" | grep -v '\.env\.example'; then bad "sensitive path tracked"; else ok "none"; fi

note "4. Secret patterns anywhere in history"
hits=0
while read -r b; do
  git cat-file -p "$b" 2>/dev/null | grep -aqIE "$SECRETS" && { echo "  blob $b"; hits=1; }
done < <(git rev-list --all --objects | awk '{print $1}' | sort -u \
         | git cat-file --batch-check='%(objectname) %(objecttype)' 2>/dev/null \
         | awk '$2=="blob"{print $1}')
[ "$hits" -eq 1 ] && bad "secret found in history — ROTATE the credential, then rewrite history" || ok "none"

note "5. Sensitive paths anywhere in history"
if git log --all --pretty=format: --name-only --diff-filter=A | sort -u \
   | grep -aE "$PATHS" | grep -v '\.env\.example'; then
  bad "sensitive path exists in history — purge with filter-branch/filter-repo"
else ok "none"; fi

printf '\n'
[ "$fail" -eq 0 ] && echo "CLEAN — safe to push." || echo "FINDINGS ABOVE — do not push until resolved."
exit "$fail"
