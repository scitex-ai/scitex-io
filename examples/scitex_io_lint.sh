#!/usr/bin/env bash
# scitex_io_lint.sh
# -----------------
# Claude Code PostToolUse hook: run the scitex-io lint rules (shipped
# inside scitex-dev's linter) against every Python file that Claude
# touches.
#
# Exit codes (Claude Code hook convention):
#   2 = block — Claude sees the rule output on stderr and must fix
#   0 = pass — warnings are still surfaced on stderr but don't block
#
# Install:
#   1. cp examples/scitex_io_lint.sh ~/.claude/hooks/post-tool-use/
#   2. chmod +x ~/.claude/hooks/post-tool-use/scitex_io_lint.sh
#   3. Wire it up in ~/.claude/settings.json (or <project>/.claude/
#      settings.json) under hooks.PostToolUse with a matcher of
#      "Edit|Write|MultiEdit". See the README "Claude Code Integration
#      as a Hook" section for the JSON snippet.
#
# Requires: scitex-dev on PATH (already a hard dep of scitex-io).

set -euo pipefail

INPUT=$(cat)

FILE=$(echo "$INPUT" | python3 -c \
    "import json,sys;print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" \
    2>/dev/null || true)

# Nothing to lint if the tool didn't touch a file or it isn't Python.
[[ -n "$FILE" && -f "$FILE" && "$FILE" == *.py ]] || exit 0

# Errors block the turn; warnings are advisory.
scitex-dev linter check-files "$FILE" --category io --severity error --no-color >&2 || exit 2
scitex-dev linter check-files "$FILE" --category io --severity warning --no-color >&2 || true

exit 0
