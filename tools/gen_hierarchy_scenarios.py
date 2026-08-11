#!/usr/bin/env python3
"""Generate the hierarchical-classification seed scenarios: CC0 media + made-up annotations.

Media is the public-domain NOAA Okeanos Explorer dive-11 fish clip (CC0 1.0, Wikimedia Commons),
fetched and cut by okeanos_media. The tracks, type hierarchy, and malformed payloads are invented
here. Everything lands under the gitignored generated root, so no binaries are checked in.

  python3 tools/gen_hierarchy_scenarios.py [--root <dir>] [--force]

Requires ffmpeg and network access on the first run; afterwards it is a no-op.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import sys
from pathlib import Path

import okeanos_media

KIT = Path(__file__).resolve().parents[1]
GENERATED_ROOT = Path(os.environ.get("DIVE_DEVKIT_GENERATED") or KIT / ".generated")
DEFAULT_ROOT = GENERATED_ROOT / "hierarchical-classification"

FRAMES = [0, 48, 96, 144, 192, 240, 288, 336]
FRAME_PATTERN = "hierarchy-frame-%03d.jpg"

# Two 3-level trees and one 2-level tree, so roll-up has somewhere to go in both directions.
VALID_HIERARCHY = {
    "juvenile-red-snapper": "red-snapper",
    "red-snapper": "fish",
    "bluefin-tuna": "tuna",
    "tuna": "fish",
    "bottlenose-dolphin": "dolphin",
    "dolphin": "mammal",
}

# One payload per branch of the normalizer (client dive-common/typeHierarchy.ts and its server
# mirror). Every DIVE write path rejects these; the viewer only ever sees one if it is planted
# into folder metadata behind DIVE's back. The comment is the reason string each one produces.
MALFORMED_HIERARCHIES = {
    "cycle": {"fish": "animal", "animal": "fish"},  # cycle animal -> fish -> animal
    "array-not-object": ["red-snapper", "fish"],  # expected an object
    "empty-child": {"   ": "fish"},  # empty child
    "empty-parent": {"red-snapper": "   "},  # empty parent for "red-snapper"
    "parent-not-string": {"red-snapper": 42},  # parent for "red-snapper" must be a string
    "self-edge": {"red-snapper": "fish", "fish": "fish"},  # self edge "fish -> fish"
}

# Each track carries a full confidence vector spanning its branch of the tree, which is what makes
# threshold roll-up and non-monotone selection observable in the viewer.
TRACK_SPECS = [
    {
        "id": 1,
        "pairs": [["juvenile-red-snapper", 0.6], ["red-snapper", 0.8], ["fish", 0.95]],
        "origin": [10, 10],
    },
    {
        "id": 2,
        "pairs": [["bluefin-tuna", 0.9], ["tuna", 0.2], ["fish", 0.8]],
        "origin": [140, 20],
    },
    {
        "id": 3,
        "pairs": [["bottlenose-dolphin", 0.85], ["dolphin", 0.75], ["mammal", 0.4]],
        "origin": [270, 30],
    },
]


def build_tracks(frame_count: int) -> dict:
    """One box per frame per track, drifting right so playback shows motion."""
    tracks = {}
    for spec in TRACK_SPECS:
        left, top = spec["origin"]
        features = [
            {
                "frame": frame,
                "bounds": [left + frame * 12, top, left + frame * 12 + 100, top + 80],
                "keyframe": True,
            }
            for frame in range(frame_count)
        ]
        tracks[str(spec["id"])] = {
            "begin": 0,
            "end": frame_count - 1,
            "id": spec["id"],
            "features": features,
            "confidencePairs": spec["pairs"],
            "attributes": {},
        }
    # version 2 selects the current schema; without it the importer expects the legacy trackId key.
    return {"tracks": tracks, "groups": {}, "version": 2}


def build_divergent_multicam_tracks(frame_count: int) -> tuple[dict, dict]:
    """Return matching logical tracks with one deliberately divergent camera replica.

    The port payload is the canonical first-camera view.  Starboard changes only track 2's
    bluefin-tuna score, making the load warning and the subsequent repair-on-edit observable
    without obscuring the hierarchy examples with different geometry or track IDs.
    """
    port = build_tracks(frame_count)
    starboard = copy.deepcopy(port)
    starboard["tracks"]["2"]["confidencePairs"][0][1] = 0.35
    return port, starboard


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n")


def generate(root: Path = DEFAULT_ROOT, force: bool = False) -> Path:
    """Produce media + annotations + hierarchy payloads under `root`; returns `root`."""
    root.mkdir(parents=True, exist_ok=True)
    image_dir = root / "images"
    multicam_root = root / "multicam"
    if force:
        for directory in (image_dir, multicam_root):
            if directory.exists():
                shutil.rmtree(directory)
    okeanos_media.extract_frames(okeanos_media.ensure_source(), image_dir, FRAMES, FRAME_PATTERN)

    write_json(root / "multipair-tracks.annotations.json", build_tracks(len(FRAMES)))
    port_tracks, starboard_tracks = build_divergent_multicam_tracks(len(FRAMES))
    for camera, tracks in (("port", port_tracks), ("starboard", starboard_tracks)):
        camera_images = multicam_root / camera / "images"
        camera_images.mkdir(parents=True, exist_ok=True)
        for source in image_dir.iterdir():
            if source.is_file():
                shutil.copy2(source, camera_images / source.name)
        write_json(multicam_root / f"{camera}-tracks.annotations.json", tracks)
    write_json(root / "valid-three-level-forest.config.json", {"typeHierarchy": VALID_HIERARCHY})
    for name, hierarchy in MALFORMED_HIERARCHIES.items():
        write_json(root / f"{name}.config.json", {"typeHierarchy": hierarchy})
    return root


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    ap.add_argument("--force", action="store_true", help="re-cut frames even if they exist")
    args = ap.parse_args()
    root = generate(args.root, args.force)
    print(f"generated hierarchical-classification scenario in {root}")
    for path in sorted(root.iterdir()):
        label = f"{len(list(path.iterdir()))} frames" if path.is_dir() else f"{path.stat().st_size} B"
        print(f"  {path.name}  ({label})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
