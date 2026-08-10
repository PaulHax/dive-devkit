# dive-devkit

Redistributable developer kit for the DIVE worktree workflow: spin up a worktree, run tests,
bring up the Docker stack, and seed a **consistent, public test surface** (annotated images +
video) into a worktree's local Girder.

Scripts and docs only — **no binaries committed**. Every seeded dataset builds its own media from
one public-domain source clip, so a fresh clone needs nothing but `ffmpeg` and network access.

## Layout
```
dive-devkit/
  README.md
  AGENTS.md              # the runbook (worktree → test → docker → electron → seed → gotchas)
  LICENSE                # MIT
  .gitignore
  seed/seed.json         # datasets to seed (generator, media paths, frame metadata, expectations)
  skills/                # issue catalogs mined from real DIVE review cycles, progressively disclosed:
                         #   a short SKILL.md index linking to per-topic reference files.
                         #   dive-feature-planning  — seams and plan omissions, by surface
                         #   dive-code-review       — defects and drifts, by topic
                         #   Discovery: symlink into <project>/.claude/skills/ + .agents/skills/ (root wired)
  tools/
    seed_datasets.py     # idempotent, self-verifying seeder
    okeanos_media.py     # fetches the CC0 source clip; builds the video + frame-metadata surface
    gen_hierarchy_scenarios.py   # type-hierarchy scenarios cut from the same clip
    up.sh                # one-shot: stack up → wait → seed
    test.sh              # one-shot: run all test envs (server/docker + client/desktop) with a summary
    down.sh              # tear down stack (+ optional worktree removal)
```
Generated media lands under `.generated/` (gitignored; override with `DIVE_DEVKIT_GENERATED`), built
once on the first seed and reused after that.

## Quickstart
```bash
# from the workspace root (parent of dive/ and dive-devkit/)
dive-devkit/tools/up.sh <worktree>          # e.g. coco-dataset-info ; add `gpu` for GPU workers
# → brings up the stack, seeds, prints the Girder/client URLs
```
Or step by step:
```bash
# bring up a stack (see AGENTS.md), then:
uv run --with girder-client --no-project python dive-devkit/tools/seed_datasets.py
dive-devkit/tools/down.sh <worktree> --remove-worktree   # teardown
```

## Run the tests (all envs, one command)
```bash
dive-devkit/tools/test.sh <worktree>        # full non-integration gate
dive-devkit/tools/test.sh <worktree> --unit # quick server/client unit-only gate
```
Runs every selected suite even if one fails, then prints a PASS/FAIL summary and exits non-zero on any
failure. Default runs server unit/lint/type plus client unit/lint/builds. Flags: `--ci`, `--lint`,
`--build`, `--integration` (needs `GIRDER_API_KEY`), `--server-only`, `--client-only`,
`--no-provision`. Auto-runs `uv sync` / `npm ci` if a worktree isn't provisioned yet.

## Seed surface (built locally, no external library)
| Dataset | Type | Generator |
|---|---|---|
| NOAA Okeanos fish video | video | `okeanos-media` |
| NOAA Okeanos frame metadata sequence | image-sequence + frame metadata | `okeanos-media` |
| Hierarchical classification (multipair, cycle, not-an-object) | image-sequence + tracks + type hierarchy | `hierarchical-classification` |
| Synthetic multicam frame metadata | stereo image-sequence + per-camera/shared frame metadata | `multicam-frame-metadata` |
| SEFSC-SEAMAP fish taxonomy | video + 24 real tracks + 147-class type hierarchy | `sefsc-seamap` |

Most footage comes from one clip: **NOAA Okeanos Explorer EX1402 dive 11, CC0 1.0 (public
domain)**, fetched once from Wikimedia Commons; annotations and frame-metadata columns on top of it
are invented. The multicam fixture draws its own PNGs with the standard library and needs no
network at all.

The SEFSC entry is the exception and the only one with real annotations:

> SEFSC-SEAMAP-761901231-Cam2, FishTrack23 ensemble dataset (Kitware / NOAA SEFSC), **CC-BY-4.0**.
> Dawkins et al., "FishTrack23: An Ensemble Underwater Dataset for Multi-Object Tracking",
> WACV 2024, pp. 7167–7176.

Its type hierarchy is real too, derived from the public VIAME SEFSC-SEAMAP model's class list and
checked in as `seed/seamap-taxonomy.json` (147 classes) — see
[tools/derive_seamap_taxonomy.py](tools/derive_seamap_taxonomy.py) to refresh it.

The seeder is idempotent and verifies `expectedTrackCount` and `expectedFrameMetadataSources`
(non-zero exit on mismatch).

See [AGENTS.md](AGENTS.md) for the full worktree/test/docker/electron runbook and gotchas.
