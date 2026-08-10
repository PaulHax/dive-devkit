#!/usr/bin/env python3
"""Fetch the FishTrack23 SEFSC-SEAMAP clip and pair it with the SEAMAP type hierarchy.

Real annotated media: 24 tracks / 983 detections over 8 species, 1920x1080 H.264, 25.4s, 761
frames at 30fps native, annotated at 5Hz. The eight species are SEAMAP classes, so the taxonomy in
seed/sefsc-seamap-hierarchy.json applies to them directly -- a dataset whose type hierarchy is
real rather than invented.

  SEFSC-SEAMAP-761901231-Cam2, FishTrack23 ensemble dataset (Kitware / NOAA SEFSC), CC-BY-4.0.
  Dawkins et al., "FishTrack23: An Ensemble Underwater Dataset for Multi-Object Tracking",
  WACV 2024, pp. 7167-7176.

Media is fetched from the public FishTrack23 collection at seed time and never committed.
Requires network access; fails loudly when offline.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import urllib.error
import urllib.request
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
GENERATED_ROOT = Path(os.environ.get("DIVE_DEVKIT_GENERATED") or KIT / ".generated")
DEFAULT_ROOT = GENERATED_ROOT / "sefsc-seamap"
HIERARCHY_FILE = KIT / "seed" / "sefsc-seamap-hierarchy.json"

SERVER = "https://viame.kitware.com/api/v1"
FOLDER_ID = "65a19f17cf5a99794ea99c7b"  # public FishTrack23 "Sample" folder
VIDEO_ITEM_ID = "65a19f17cf5a99794ea99c7a"
VIDEO_NAME = "SEFSC-SEAMAP-761901231-Cam2.mp4"
UA = "dive-devkit/1.0 (DIVE local test surface; CC-BY-4.0 media fetch)"


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(request, timeout=180) as response, dest.open("wb") as out:
            shutil.copyfileobj(response, out)
    except urllib.error.URLError as exc:
        raise SystemExit(f"cannot reach {url}: {exc.reason}") from exc


def generate(root: Path = DEFAULT_ROOT, force: bool = False) -> Path:
    root.mkdir(parents=True, exist_ok=True)

    video = root / VIDEO_NAME
    if force or not video.exists():
        print(f"  downloading CC-BY-4.0 clip -> {video}")
        _download(f"{SERVER}/item/{VIDEO_ITEM_ID}/download", video)

    # DIVE stores these annotations as documents, not files, so they come from the export
    # endpoint rather than the folder listing.
    annotations = root / "annotations.viame.csv"
    if force or not annotations.exists():
        print(f"  exporting annotations -> {annotations}")
        _download(
            f"{SERVER}/dive_annotation/export"
            f"?folderId={FOLDER_ID}&excludeBelowThreshold=false",
            annotations,
        )
    rows = [
        line for line in annotations.read_text().splitlines()
        if line and not line.startswith("#")
    ]
    if not rows:
        raise SystemExit("annotation export returned no detections")

    hierarchy = json.loads(HIERARCHY_FILE.read_text())["typeHierarchy"]
    (root / "config.json").write_text(
        json.dumps({"typeHierarchy": hierarchy}, indent=2, sort_keys=True) + "\n"
    )
    return root


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    ap.add_argument("--force", action="store_true", help="re-download even if present")
    args = ap.parse_args()
    root = generate(args.root, args.force)
    print(f"generated sefsc-seamap dataset in {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
