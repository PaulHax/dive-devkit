#!/usr/bin/env python3
"""CC0 NOAA Okeanos source media, and the seed surface built from it.

One public clip backs every media-bearing scenario in the kit: NOAA Okeanos Explorer EX1402
dive 11, CC0 1.0 (public domain), fetched once from Wikimedia Commons into .generated/media.

`generate()` produces the video dataset, a 16-frame image sequence cut from the same clip, and a
frame-metadata sidecar keyed by image filename. `ensure_source` and `extract_frames` are shared
with gen_hierarchy_scenarios.

Requires ffmpeg and network access on the first run; afterwards it is a no-op.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import urllib.request
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
GENERATED_ROOT = Path(os.environ.get("DIVE_DEVKIT_GENERATED") or KIT / ".generated")
DEFAULT_ROOT = GENERATED_ROOT / "okeanos"

# NOAA Okeanos Explorer EX1402 dive 11, CC0 1.0 (public domain).
SOURCE_URL = "https://commons.wikimedia.org/wiki/Special:FilePath/Ex1402-dive11_fish.webm"
SOURCE_NAME = "ex1402-dive11-fish.webm"
UA = "dive-devkit/1.0 (DIVE local test surface; CC0 media fetch)"
SOURCE_FPS = 24000 / 1001  # 23.976...

# One frame per second of source, which is what makes the sidecar's elapsed_s column line up.
# The clip is 345 frames, so frame 336 is the last one a stride of 24 can reach.
STRIDE = 24
FRAME_COUNT = 15
FRAME_PATTERN = "ex1402-dive11-fish-frame-%03d.jpg"
SCALE_WIDTH = 640

# Invented values describing the real footage: a fish crossing a sand/silt seafloor. The columns
# exercise the join (filename), a counter join (source_frame), and mixed text/numeric display.
COLUMNS = [
    "filename",
    "elapsed_s",
    "source_frame",
    "source_date",
    "region",
    "source_depth_m",
    "subject",
    "substrate",
    "vehicle_visible",
    "scene_note",
]
SCENE_NOTES = [
    "fish entering from upper left",
    "fish approaching camera",
    "fish centered head-on",
    "fish turning broadside",
    "fish drifting toward the right edge",
    "sediment plume rising behind the fish",
    "fish holding station",
    "fish nosing at the substrate",
    "second fish entering at the lower right",
    "both fish in frame",
    "lead fish leaving the frame",
    "sediment settling",
    "open water, no subject",
    "fish returning from the right",
    "fish passing under the vehicle",
    "fish out of frame, substrate only",
]


def ensure_source(dest: Path | None = None) -> Path:
    """Fetch the CC0 clip once; returns its path."""
    dest = dest or GENERATED_ROOT / "media" / SOURCE_NAME
    if dest.exists():
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"  downloading CC0 source video -> {dest}")
    request = urllib.request.Request(SOURCE_URL, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=180) as response, dest.open("wb") as out:
        shutil.copyfileobj(response, out)
    return dest


def extract_frames(
    source: Path,
    image_dir: Path,
    frames: list[int],
    pattern: str,
    width: int = SCALE_WIDTH,
) -> None:
    """Cut `frames` (source frame numbers) out of `source` into `image_dir` as JPEGs."""
    expected = {pattern % index for index in range(1, len(frames) + 1)}
    if image_dir.is_dir() and {p.name for p in image_dir.glob("*.jpg")} == expected:
        return
    if shutil.which("ffmpeg") is None:
        raise SystemExit("ffmpeg is required to cut the CC0 source video into frames")
    if image_dir.exists():
        shutil.rmtree(image_dir)
    image_dir.mkdir(parents=True)
    select = "+".join(f"eq(n\\,{frame})" for frame in frames)
    print(f"  extracting {len(frames)} frames -> {image_dir}")
    subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error",
            "-i", str(source),
            "-vf", f"select={select},scale={width}:-2",
            "-vsync", "0", "-q:v", "4",
            str(image_dir / pattern),
        ],
        check=True,
    )
    actual = {p.name for p in image_dir.glob("*.jpg")}
    if actual != expected:
        raise SystemExit(f"frame extraction mismatch: missing={sorted(expected - actual)}")


def build_frame_metadata(frames: list[int]) -> str:
    rows = [",".join(COLUMNS)]
    for index, frame in enumerate(frames):
        rows.append(
            ",".join(
                [
                    FRAME_PATTERN % (index + 1),
                    f"{frame / SOURCE_FPS:.3f}",
                    str(frame),
                    "2014-04-23",
                    "North-central Gulf of Mexico",
                    f"{28.0 + index * 0.4:.1f}",
                    "fish",
                    "sand/silt",
                    "false",
                    SCENE_NOTES[index % len(SCENE_NOTES)],
                ]
            )
        )
    return "\n".join(rows) + "\n"


def generate(root: Path = DEFAULT_ROOT, force: bool = False) -> Path:
    """Produce the video, the image sequence, and its frame-metadata sidecar under `root`."""
    root.mkdir(parents=True, exist_ok=True)
    source = ensure_source()
    frames = [index * STRIDE for index in range(FRAME_COUNT)]

    video_dir = root / "video"
    video_dir.mkdir(parents=True, exist_ok=True)
    video = video_dir / SOURCE_NAME
    if not video.exists():
        shutil.copyfile(source, video)

    image_dir = root / "frame-metadata-sequence"
    if force and image_dir.exists():
        shutil.rmtree(image_dir)
    extract_frames(source, image_dir, frames, FRAME_PATTERN)

    sidecar_dir = root / "frame-metadata"
    sidecar_dir.mkdir(parents=True, exist_ok=True)
    (sidecar_dir / "frame_metadata.csv").write_text(build_frame_metadata(frames))
    return root


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    ap.add_argument("--force", action="store_true", help="re-cut frames even if they exist")
    args = ap.parse_args()
    root = generate(args.root, args.force)
    print(f"generated okeanos media in {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
