#!/bin/sh
set -eu

# Template snippet for .githooks/pre-commit or an existing pre-commit script.
# Requires scripts/check-autoresearch-protected.py and
# .harness/autoresearch-protected.txt to exist in the project.
python3 scripts/check-autoresearch-protected.py --pre-commit
