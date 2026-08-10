#!/usr/bin/env bash
# Tear down a worktree's DIVE stack; optionally remove the worktree itself.
# Usage: tools/down.sh <worktree> [--remove-worktree]
set -euo pipefail

WT="${1:?usage: down.sh <worktree> [--remove-worktree]}"
KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIVE="$(dirname "$KIT")/dive"

if [ -d "$DIVE/$WT" ]; then
  ( cd "$DIVE/$WT" && docker compose --profile cpu --profile gpu down -v ) || true
fi

if [ "${2:-}" = "--remove-worktree" ]; then
  cd "$DIVE"
  git worktree remove --force "./$WT" 2>/dev/null || true
  # Docker leaves root-owned files in the bind-mounted ./server; delete them as root via a container.
  [ -d "$DIVE/$WT" ] && docker run --rm -v "$DIVE:/work" redis:latest rm -rf "/work/$WT"
  git branch -D "$WT" 2>/dev/null || true
  git worktree prune
  echo "removed worktree $WT"
fi
