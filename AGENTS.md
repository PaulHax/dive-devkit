# DIVE devkit runbook (agent notes)

Set up a DIVE worktree, run tests, bring up the stack/Electron, and seed a consistent test
surface. Paths are relative to the **workspace root** (the parent of `dive/` and `dive-devkit/`).

Bare repo: `dive/.git` → `.bare`. Remotes: `origin`=Kitware/dive, `mine`=PaulHax/dive.
Server cmds run in `dive/<wt>/server`, client cmds in `dive/<wt>/client`.

## One-shot
```bash
dive-devkit/tools/up.sh   <wt> [cpu|gpu]            # fetch media → stack up → wait → seed
dive-devkit/tools/test.sh <wt> [--unit|--ci|--integration]   # run test gates, one summary
dive-devkit/tools/down.sh <wt> [--remove-worktree]
```
Everything below is the manual breakdown.

## Provision (per worktree, one-time)
```bash
cd dive/<wt>/server && uv sync --group dev        # ~555M .venv, <2s warm cache
cd dive/<wt>/client && npm ci
```

## Tests
```bash
# full non-integration gate, one summary:
dive-devkit/tools/test.sh <wt>            # add --integration for live-stack integration
                                          # add --unit/--quick for server+client unit only
                                          # add --ci for GitHub Actions parity
                                          # --server-only | --client-only | --no-provision
```
Runs each selected suite even if an earlier one fails, prints PASS/FAIL per suite, exits non-zero on
any failure. Default = server unit/lint/type plus client unit/lint/builds (no live stack needed).
`--ci` mirrors GitHub Actions and skips server lint/type because CI does not run them.
Do not treat integration as part of the default local gate; it mutates a live stack and needs private
fixture access.
The manual breakdown of each suite:
```bash
# server unit
cd dive/<wt>/server && uv run tox -e testunit
uv run tox -e lint ; uv run tox -e type ; uv run tox -e format   # not in CI

# client unit (23 specs)
cd dive/<wt>/client && npm test
npm run lint ; npm run lint:templates
./checkbuild.sh                                                   # lint+test+build gate

# server integration — mutates local Girder; downloads private fixtures from viame.kitware.com
docker compose --profile gpu up -d
export GIRDER_API_KEY=<read-only> ; uv run tox -e testintegration
```

## CI (`client/.github/workflows/blank.yml`)
- client(web): `npm ci` · `npm run lint` · `npm run lint:templates` · `npm test -- --coverage` · `npm run build:web`
- client(electron): `npm ci` · `npm run build:electron -- --linux AppImage`
- server: `tox -e testunit` (py3.11)
- NOT in CI: server `lint`/`type`, integration. No cypress/e2e suite exists.

## Docker stack (one at a time)
```bash
docker rm -f traefik autoheal                     # fixed-name containers; free them first
cd dive/<wt>
cp .env.default .env                              # set unique COMPOSE_PROJECT_NAME=<wt> (see gotchas)
docker compose --profile gpu up -d                # gpu=all 3 workers; cpu=default worker only
# Girder http://localhost:8010 (admin/letmein); fresh stack = empty mongo
# girder hot-reloads ./server; workers don't → docker compose up -d girder_worker_pipelines
docker compose down                               # add -v to wipe that project's volumes
```

## Seed datasets (consistent, shareable surface)
Every entry builds its own media under `.generated/` (`DIVE_DEVKIT_GENERATED`, gitignored) — the kit
reads no external media library. Seed list: `dive-devkit/seed/seed.json`. First run downloads one
CC0 clip and needs **`ffmpeg`**; after that it is offline and idempotent.
```bash
# stack up + girder ready, then:
uv run --with girder-client --no-project python dive-devkit/tools/seed_datasets.py
uv run --with girder-client --no-project python dive-devkit/tools/seed_datasets.py --only okeanos
```
- Seeder is idempotent (skips by name; `--force` re-uploads). Recipe: `createFolder{fps,type}` →
  upload media and declared `frameMetadata` sidecars → `dive_rpc/postprocess` with
  **`skipJobs=False`** (required: DIVE sets the `annotate`/DatasetMarker only on that path; videos
  transcode+wait). Self-verifies `expectedTrackCount` and `expectedFrameMetadataFrames` → exit 1 on
  mismatch. Writes `seed/seeded-local.json` (name→id+viewer+tracks/frame-metadata counts).
Surface: NOAA video (CC0) + NOAA real-frame image sequence with frame metadata + three
hierarchical-classification datasets + synthetic multicam frame-metadata fixture.

### Generators
Every seed entry names one in `"generate"`, and all paths are `{"root": "generated", "path": …}`.

- `okeanos-media` — `tools/okeanos_media.py`. Owns the CC0 source clip (NOAA Okeanos Explorer
  EX1402 dive 11, Wikimedia Commons), fetched once into `.generated/media`. Emits the video, a
  16-frame sequence (every 24th frame, one per second), and a filename-keyed
  `frame_metadata.csv` whose columns are invented.
- `hierarchical-classification` — `tools/gen_hierarchy_scenarios.py`. Cuts 8 frames from the same
  clip via `okeanos_media`, and writes made-up multipair tracks plus one hierarchy payload per
  branch of the normalizer (valid forest + 6 malformed).
- `multicam-frame-metadata` — synthetic PNGs written with the stdlib (`write_png`), no network.
- `sefsc-seamap` — `tools/sefsc_seamap.py`. The only entry with **real annotations**: fetches the
  FishTrack23 SEFSC clip (24 tracks / 983 detections / 8 species, CC-BY-4.0) from the public
  collection, exports its annotations via `dive_annotation/export` (DIVE stores them as documents,
  not files, so they are not in the folder listing), and writes a `config.json` carrying the real
  type hierarchy.

Type-hierarchy specifics — where the taxonomy JSON comes from, the digit-zeroing parent rule, and
how malformed-hierarchy datasets are planted — live in `seed/type-hierarchy.md`.

**Anything new must generate its own data.** The kit takes no dependency on a sibling media library,
so third-party media it cannot fabricate (VIAME, SEFSC) is out of scope — point those at a live
DIVE instance instead of seeding them here.

## Client dev server
```bash
cd dive/<wt>/client
VITE_PORT=3000 VITE_API_PROXY_TARGET=http://localhost:8010 npm run serve   # http://localhost:3000
```

## Electron desktop (local FS, no stack needed)
```bash
cd dive/<wt>/client
npm run serve:electron                            # boots app + desktop backend
npm run build:electron -- --linux AppImage        # CI gate
# desktop logic covered headless by platform/desktop/* specs in `npm test`
```

## Gotchas
- **8080 = dive-dsa**, never use. Client serve AND electron renderer both default to 8080 → always pass `VITE_PORT=3000` (electron auto-falls back to 8081).
- **`.env.default` sets `COMPOSE_PROJECT_NAME=dive`** → every worktree using a fresh copy shares project `dive` (containers `dive-*`, volumes `dive_*`), so stacks are NOT per-worktree. Set unique `COMPOSE_PROJECT_NAME=<wt>` in `.env` (what `up.sh` does) for isolation.
- **Docker writes ROOT-OWNED files into bind-mounted `./server`** (`__pycache__`, `dive_server/dive_client`) → breaks `git worktree remove`/`rm`. Down the stack first; if a dir is stuck (host sudo needs a password here): `docker run --rm -v <abs>/dive:/work redis:latest rm -rf /work/<wt>` (this is what `down.sh --remove-worktree` does).
- **uv**: always `uv run tox` (no global tox/pipx); needs `uv sync --group dev` first.
- **Version drift**: tests pass on older local toolchains, but builds need `.nvmrc` node and py3.11.
- **Seed media is public/shareable — never commit bytes or a `GIRDER_API_KEY`.** The DIVE integration-test fixtures (alice/bobby/kwcoco) are **private** (403 for non-internal accounts) — not used. **Don't share a live Mongo across worktrees** (branch migration drift corrupts it); seed each worktree's own DB.
