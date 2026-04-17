#!/bin/bash
# protect-global-methodology-bash.sh — block Bash-based writes to upstream-managed
# global rules files. Catches cp, mv, sed -i, tee, python -c "open(...,'w')",
# echo > redirects. Companion to protect-global-methodology.sh.

command -v jq >/dev/null || { echo "BLOCKED: jq required for protect-global-methodology-bash.sh" >&2; exit 1; }

PROTECTED_PATTERNS=(
  "\.claude/rules/common/harness-methodology\.md"
)

COMMAND=$(echo "$CLAUDE_TOOL_INPUT" | jq -r '.command // empty')
[ -z "$COMMAND" ] && exit 0

WRITE_VERBS='(\bcp\b|\bmv\b|sed -i|\btee\b|>|>>|python.* -c .*open\([^)]*,[^)]*["\x27]w|chmod[[:space:]]+[0-9]*[+]?w)'
for pattern in "${PROTECTED_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qE "$WRITE_VERBS" && echo "$COMMAND" | grep -qE "$pattern"; then
    cat >&2 <<EOF
BLOCKED: write command targets upstream-managed snapshot ($pattern).
Edit ~/.claude/rules/common/harness-operations.md instead, or update via repo's install.sh.
EOF
    exit 1
  fi
done
exit 0
