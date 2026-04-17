#!/bin/bash
# protect-global-methodology.sh — block Edit/Write on upstream-managed global rules.
# Invoked as a global PreToolUse hook with $CLAUDE_TOOL_INPUT JSON.
#
# Why this exists: ~/.claude/rules/common/harness-methodology.md is a snapshot of
# docs/methodology.md from the claude-code-harness repo. Users should extend
# their harness via harness-operations.md (user-editable overlay), not by
# editing the upstream snapshot. Editing the snapshot causes drift from the
# upstream source of truth.
#
# Self-application of P5 ladder level 3: drift is not prevented by a rule
# ("don't edit this file"), but by structurally blocking the edit attempt.

command -v jq >/dev/null || { echo "BLOCKED: jq required for protect-global-methodology.sh" >&2; exit 1; }

PROTECTED_BASENAMES=(
  "harness-methodology.md"
)

# Match only under the global rules directory; do not block same-named files
# in user projects.
PROTECTED_PATH_SUFFIXES=(
  ".claude/rules/common/harness-methodology.md"
)

FILE_PATH=$(echo "$CLAUDE_TOOL_INPUT" | jq -r '.file_path // empty')
[ -z "$FILE_PATH" ] && exit 0

BASENAME=$(basename "$FILE_PATH")
for b in "${PROTECTED_BASENAMES[@]}"; do
  if [ "$BASENAME" = "$b" ]; then
    for suffix in "${PROTECTED_PATH_SUFFIXES[@]}"; do
      if [[ "$FILE_PATH" == *"$suffix" ]]; then
        cat >&2 <<EOF
BLOCKED: $FILE_PATH is an upstream-managed snapshot.

Editing this file causes drift from the claude-code-harness source of truth
(docs/methodology.md). To extend the harness with your own operational rules,
edit the user overlay instead:

  ~/.claude/rules/common/harness-operations.md

Both files are auto-loaded. To update the upstream snapshot, pull the repo and
re-run its install.sh.
EOF
        exit 1
      fi
    done
  fi
done
exit 0
