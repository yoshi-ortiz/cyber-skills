#!/usr/bin/env bash
# Install the companion files this harness needs into the brainstorming skill.
#
# The harness does not ship a companion, but it does require two things from
# one, and the stock files provide neither:
#
#   1. server.cjs must BROADCAST each decision and GREET each new connection
#      with the ledger's current state. Without the broadcast, one browser's
#      click is invisible to every other; without the greeting, a browser
#      opened later starts from whatever snapshot was baked into its page.
#   2. start-server.sh must retire the project's previous server before binding
#      a new one. The stock script looks for it in a pid file under the session
#      directory, and the session id is minted fresh on every run, so the file
#      never exists and the kill has never once fired -- every restart leaves
#      another live server, each with its own client set, and two browsers that
#      land on two ports can never agree.
#
# Both live here because they are not in any repository of their own. Re-run
# this after anything resets ~/.agents/skills/brainstorming.
#
# Usage: ./install.sh [path-to-brainstorming-skill]

set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"

TARGET="${1:-}"
if [[ -z "$TARGET" ]]; then
  for c in "$HOME/.agents/skills/brainstorming" "$HOME/.claude/skills/brainstorming"; do
    [[ -d "$c/scripts" ]] && { TARGET="$c"; break; }
  done
fi
if [[ -z "$TARGET" || ! -d "$TARGET/scripts" ]]; then
  echo "error: pass the brainstorming skill path (no scripts/ dir found)" >&2
  exit 1
fi

STAMP="$(date +%Y%m%d-%H%M%S)"
for f in server.cjs start-server.sh; do
  if [[ -f "$TARGET/scripts/$f" ]] && ! cmp -s "$HERE/$f" "$TARGET/scripts/$f"; then
    cp "$TARGET/scripts/$f" "$TARGET/scripts/$f.bak-$STAMP"
    echo "backed up $f -> $f.bak-$STAMP"
  fi
  cp "$HERE/$f" "$TARGET/scripts/$f"
  echo "installed $f"
done
chmod +x "$TARGET/scripts/start-server.sh"

echo
echo "Restart the companion so the new server is the one running:"
echo "  $TARGET/scripts/start-server.sh --project-dir \"\$PWD\""
echo "Then: bootstrap_harness.py doctor --project-root ."
