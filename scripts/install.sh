#!/bin/bash
# install.sh — install claude-code-harness into ~/.claude.
#
# Boundary model:
#   - Upstream-managed (locked, immutable in user env):
#       ~/.claude/rules/common/harness-methodology.md  ← snapshot of docs/methodology.md
#       ~/.claude/docs/harness-reference.md            ← snapshot of docs/reference.md
#       ~/.claude/skills/{autoresearch,harness-engineer,multi-review}/
#       ~/.claude/commands/init-harness.md
#   - User-editable (never overwritten by re-install):
#       ~/.claude/rules/common/harness-operations.md   ← seeded from docs/operations-template.md on first install
#       ~/.claude/hooks/protect-global-methodology{,-bash}.sh  ← copied once, user may customize
#
# Safe to re-run. Use this script for updates: it chmods upstream files read-only,
# seeds the overlay only if absent, and prints a summary of what changed.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GLOBAL_CLAUDE="${HOME}/.claude"

log() { printf '  %s\n' "$1"; }
ok()  { printf '  ✓ %s\n' "$1"; }
warn() { printf '  ! %s\n' "$1" >&2; }

echo "claude-code-harness installer"
echo "  repo:   ${REPO_ROOT}"
echo "  target: ${GLOBAL_CLAUDE}"
echo

# --- Upstream layer: methodology + reference -------------------------------
echo "Upstream layer (locked):"
mkdir -p "${GLOBAL_CLAUDE}/rules/common" "${GLOBAL_CLAUDE}/docs"

for pair in \
  "docs/methodology.md:rules/common/harness-methodology.md" \
  "docs/reference.md:docs/harness-reference.md"
do
  src="${REPO_ROOT}/${pair%%:*}"
  dst="${GLOBAL_CLAUDE}/${pair##*:}"
  [ -f "$src" ] || { warn "missing source: $src"; continue; }
  # Make writable before overwrite so re-install works
  [ -f "$dst" ] && chmod u+w "$dst" 2>/dev/null || true
  cp "$src" "$dst"
  chmod 444 "$dst"
  ok "$dst (chmod 444)"
done

# --- Upstream layer: skills + commands -------------------------------------
mkdir -p "${GLOBAL_CLAUDE}/skills" "${GLOBAL_CLAUDE}/commands"
if [ -d "${REPO_ROOT}/skills" ]; then
  cp -R "${REPO_ROOT}/skills/." "${GLOBAL_CLAUDE}/skills/"
  ok "${GLOBAL_CLAUDE}/skills/ (autoresearch, harness-engineer, multi-review)"
fi
if [ -f "${REPO_ROOT}/commands/init-harness.md" ]; then
  cp "${REPO_ROOT}/commands/init-harness.md" "${GLOBAL_CLAUDE}/commands/init-harness.md"
  ok "${GLOBAL_CLAUDE}/commands/init-harness.md"
fi

# --- User overlay: harness-operations.md (seed only if absent) -------------
echo
echo "User overlay (editable):"
OVERLAY="${GLOBAL_CLAUDE}/rules/common/harness-operations.md"
if [ -f "$OVERLAY" ]; then
  ok "$OVERLAY (preserved — not overwritten)"
else
  cp "${REPO_ROOT}/docs/operations-template.md" "$OVERLAY"
  ok "$OVERLAY (seeded from template)"
fi

# --- Protect hooks: copy once, do not overwrite user edits -----------------
echo
echo "Protect hooks:"
mkdir -p "${GLOBAL_CLAUDE}/hooks"
for h in protect-global-methodology.sh protect-global-methodology-bash.sh; do
  src="${REPO_ROOT}/hooks/${h}"
  dst="${GLOBAL_CLAUDE}/hooks/${h}"
  [ -f "$src" ] || { warn "missing source hook: $src"; continue; }
  if [ -f "$dst" ]; then
    ok "$dst (preserved)"
  else
    cp "$src" "$dst"
    chmod +x "$dst"
    ok "$dst (installed)"
  fi
done

# --- Settings.json hook registration: print only, do not auto-edit ---------
SETTINGS="${GLOBAL_CLAUDE}/settings.json"
REGISTERED=0
if [ -f "$SETTINGS" ] && grep -q "protect-global-methodology.sh" "$SETTINGS" 2>/dev/null; then
  REGISTERED=1
fi

echo
echo "Hook registration in ${SETTINGS}:"
if [ "$REGISTERED" = "1" ]; then
  ok "already registered"
else
  cat <<'EOF'
  ! not registered. Add the following to your ~/.claude/settings.json under
    "hooks.PreToolUse" to activate the protection:

  {
    "hooks": {
      "PreToolUse": [
        {
          "matcher": "Edit|Write",
          "hooks": [{"type": "command", "command": "bash ~/.claude/hooks/protect-global-methodology.sh"}]
        },
        {
          "matcher": "Bash",
          "hooks": [{"type": "command", "command": "bash ~/.claude/hooks/protect-global-methodology-bash.sh"}]
        }
      ]
    }
  }

  Without the hook, methodology.md is still chmod 444, which blocks casual
  edits but not `chmod +w` followed by overwrite. The hook closes that gap.
EOF
fi

echo
echo "Done."
