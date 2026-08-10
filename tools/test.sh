#!/usr/bin/env bash
# Run DIVE test suites for a worktree across envs in one shot.
#   server/docker env -> server unit/lint/type gates (pytest/flake8/mypy via tox)
#   client/desktop env -> client unit/lint/build gates (vitest/eslint/vite/electron)
# Runs every selected suite even if an earlier one fails, then prints a pass/fail summary
# and exits non-zero if anything failed.
#
# Usage: tools/test.sh <worktree> [options]
#   (default)         full non-integration gate: server unit/lint/type + client unit/lint/builds
#   --unit            quick unit-only gate: server unit + client/desktop unit
#   --quick           alias for --unit
#   --ci              GitHub Actions parity: units + client lint + client builds
#   --integration     also: server integration tests (needs GIRDER_API_KEY + a live stack)
#   --server-only     skip client suites
#   --client-only     skip server suites
#   --no-provision    don't auto `uv sync` / `npm ci` when deps are missing
set -uo pipefail   # deliberately NOT -e: collect all results, report at the end

WT="${1:?usage: test.sh <worktree> [--unit|--quick|--ci|--lint|--build|--integration|--server-only|--client-only|--no-provision]}"
shift || true
KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WTDIR="$(dirname "$KIT")/dive/$WT"
SRV="$WTDIR/server"; CLI="$WTDIR/client"
[ -d "$WTDIR" ] || { echo "no worktree at $WTDIR" >&2; exit 1; }

SERVER_UNIT=1 CLIENT_UNIT=1 CLIENT_LINT=1 SERVER_LINT=1 BUILD=1 INTEGRATION=0 PROVISION=1
for a in "$@"; do case "$a" in
  --unit|--quick) CLIENT_LINT=0; SERVER_LINT=0; BUILD=0 ;;
  --lint)         CLIENT_LINT=1; SERVER_LINT=1 ;;
  --build)        BUILD=1 ;;
  --ci)           CLIENT_LINT=1; SERVER_LINT=0; BUILD=1 ;;
  --integration)  INTEGRATION=1 ;;
  --server-only)  CLIENT_UNIT=0; CLIENT_LINT=0; BUILD=0 ;;
  --client-only)  SERVER_UNIT=0; SERVER_LINT=0; INTEGRATION=0 ;;
  --no-provision) PROVISION=0 ;;
  *) echo "unknown option: $a" >&2; exit 2 ;;
esac; done

NAMES=(); CODES=()
run() {  # run <label> <dir> <cmd...>
  local label="$1" dir="$2"; shift 2
  printf '\n\033[1m════════ %s ════════\033[0m\n' "$label"
  ( cd "$dir" && "$@" ); local rc=$?
  NAMES+=("$label"); CODES+=("$rc")
}

if [ "$PROVISION" = 1 ]; then
  { [ "$SERVER_UNIT" = 1 ] || [ "$SERVER_LINT" = 1 ] || [ "$INTEGRATION" = 1 ]; } \
    && [ ! -d "$SRV/.venv" ] && run "provision: uv sync --group dev" "$SRV" uv sync --group dev
  { [ "$CLIENT_UNIT" = 1 ] || [ "$CLIENT_LINT" = 1 ] || [ "$BUILD" = 1 ]; } \
    && [ ! -d "$CLI/node_modules" ] && run "provision: npm ci" "$CLI" npm ci
fi

[ "$SERVER_UNIT" = 1 ] && run "server unit (tox testunit)"            "$SRV" uv run tox -e testunit
[ "$SERVER_LINT" = 1 ] && run "server lint (flake8)"                  "$SRV" uv run tox -e lint
[ "$SERVER_LINT" = 1 ] && run "server type (mypy)"                    "$SRV" uv run tox -e type
[ "$CLIENT_UNIT" = 1 ] && run "client + desktop unit (vitest)"        "$CLI" npm test
[ "$CLIENT_LINT" = 1 ] && run "client lint (eslint)"                  "$CLI" npm run lint
[ "$CLIENT_LINT" = 1 ] && run "client lint:templates"                "$CLI" npm run lint:templates
[ "$BUILD" = 1 ]       && run "client build:web"                      "$CLI" npm run build:web
[ "$BUILD" = 1 ]       && run "client build:electron (AppImage)"      "$CLI" npm run build:electron -- --linux AppImage
if [ "$INTEGRATION" = 1 ]; then
  [ -n "${GIRDER_API_KEY:-}" ] || echo "warning: GIRDER_API_KEY unset — integration tests will fail/skip" >&2
  run "server integration (tox testintegration)" "$SRV" uv run tox -e testintegration
fi

printf '\n\033[1m──────── summary (%s) ────────\033[0m\n' "$WT"
fail=0
for i in "${!NAMES[@]}"; do
  if [ "${CODES[$i]}" = 0 ]; then printf '  \033[32mPASS\033[0m  %s\n' "${NAMES[$i]}"
  else printf '  \033[31mFAIL\033[0m  %s (exit %s)\n' "${NAMES[$i]}" "${CODES[$i]}"; fail=1; fi
done
exit $fail
