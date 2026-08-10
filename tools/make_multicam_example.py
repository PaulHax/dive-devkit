#!/usr/bin/env python3
"""Package the synthetic multicam fixture as a shareable example for manual upload testing.

DIVE cannot create a multicam dataset from a zip upload (zips always become regular
datasets); multicam is created through the web Upload screen's multicam dialog, which
takes one folder per camera. This tool builds that folder tree — the same bytes the
seeder uploads — plus a README, and zips it for easy sharing/moving:

    .generated/multicam-example/            # extract-and-point-the-dialog-here tree
    .generated/multicam-example.zip

Usage:
    python3 tools/make_multicam_example.py
"""
from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

from seed_datasets import GENERATED_ROOT, generate_multicam_frame_metadata_fixture

README = """\
# DIVE multicam example (stereo, image sequence)

Synthetic stereo dataset: 4 frames per camera, camera-local frame metadata
sidecars, and a shared parent-level frame metadata file.

DIVE does NOT create multicam datasets from zip uploads — extract this zip,
then in the DIVE web client:

1. Upload screen -> multicam import dialog, subtype Stereo.
2. Pick `port/images` for the port camera and `starboard/images` for the
   starboard camera; each folder carries its camera-local
   `frame_metadata.csv` sidecar beside the images. Set FPS to 1.
3. Import. Each camera becomes a child dataset; the parent folder is the
   multicam dataset.
4. Shared metadata: the multicam dialog cannot place a parent-level file.
   After import, open the dataset in the viewer and use
   Import -> Frame Metadata to attach `shared/frame-metadata.csv` at the
   parent level (or upload it into the parent folder via the Girder file
   browser under its reserved name). Its `port_image` / `starboard_image`
   columns join each camera's frames by image filename.

Expected Frame Info panel per camera: `local_depth_m` / `local_note` from the
camera-local sidecar plus `vehicle_altitude_m` / `shared_note` from the shared
file.
"""


def build_example() -> Path:
    generate_multicam_frame_metadata_fixture()
    fixture = GENERATED_ROOT / "multicam-frame-metadata"
    example = GENERATED_ROOT / "multicam-example"
    if example.exists():
        shutil.rmtree(example)
    shutil.copytree(fixture, example)
    # The multicam dialog takes one folder per camera, so the example keeps each
    # camera-local sidecar beside its images instead of the seeder's sidecar/ dir.
    for camera in ("port", "starboard"):
        sidecar = example / camera / "sidecar" / "frame_metadata.csv"
        sidecar.rename(example / camera / "images" / "frame_metadata.csv")
        (example / camera / "sidecar").rmdir()
    (example / "README.md").write_text(README)

    zip_path = GENERATED_ROOT / "multicam-example.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(example.rglob("*")):
            if path.is_file():
                zf.write(path, Path("multicam-example") / path.relative_to(example))
    return zip_path


if __name__ == "__main__":
    zip_path = build_example()
    print(f"wrote {zip_path}")
    print(f"tree:  {zip_path.with_suffix('')}")
