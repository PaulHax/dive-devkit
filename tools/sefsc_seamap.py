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
import csv
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
    write_hierarchical_formats(root, parse_viame(annotations), hierarchy)
    return root


def branch(label: str, hierarchy: dict) -> list[str]:
    chain, seen = [label], {label}
    while chain[-1] in hierarchy and hierarchy[chain[-1]] not in seen:
        chain.append(hierarchy[chain[-1]])
        seen.add(chain[-1])
    return chain


def parse_viame(path: Path) -> dict:
    """Group the exported detections by track id."""
    tracks: dict = {}
    for row in csv.reader(path.read_text().splitlines()):
        if not row or row[0].startswith("#"):
            continue
        track = tracks.setdefault(row[0], {"type": row[9] if len(row) > 9 else "unknown",
                                           "detections": []})
        track["detections"].append({
            "frame": int(row[2]),
            "time": row[1],
            "bounds": [float(v) for v in row[3:7]],
        })
    return tracks


def hierarchical_pairs(label: str, hierarchy: dict) -> list:
    """A confidence vector spanning the label's branch, rising toward the root.

    This is the shape a hierarchy-aware classifier emits; the published annotations carry a single
    pair at 1.0, so the ancestor confidences are synthesized here.
    """
    chain = branch(label, hierarchy)
    return [[name, round(1.0 - 0.15 * index, 2)] for index, name in enumerate(chain)]


def write_hierarchical_formats(root: Path, tracks: dict, hierarchy: dict) -> None:
    """The same tracks in every format DIVE ingests, so importers can be compared directly."""
    rows = [
        "# 1: Detection or Track-id,2: Video or Image Identifier,3: Unique Frame Identifier,"
        "4-7: Img-bbox(TL_x,TL_y,BR_x,BR_y),8: Detection or Length Confidence,"
        "9: Target Length (0 or -1 if invalid),10-11+: Repeated Species,Confidence Pairs",
        '# metadata,fps: 5.0,"exported_by: ""dive-devkit"""',
    ]
    dive_tracks = {}
    coco_annotations, coco_categories, coco_images = [], {}, {}
    for track_id, track in sorted(tracks.items(), key=lambda kv: int(kv[0])):
        pairs = hierarchical_pairs(track["type"], hierarchy)
        frames = [d["frame"] for d in track["detections"]]
        for detection in track["detections"]:
            flat = [str(part) for pair in pairs for part in pair]
            rows.append(",".join([
                track_id, detection["time"], str(detection["frame"]),
                *[f"{v:g}" for v in detection["bounds"]], "1.0", "-1", *flat,
            ]))
            coco_images.setdefault(detection["frame"], {
                "id": detection["frame"], "file_name": f"frame_{detection['frame']:06d}.png",
                "width": 1920, "height": 1080,
            })
            # COCO carries one category per annotation, so only the top pair survives.
            top = max(pairs, key=lambda pair: pair[1])
            category_id = coco_categories.setdefault(top[0], len(coco_categories) + 1)
            left, top_y, right, bottom = detection["bounds"]
            coco_annotations.append({
                "id": len(coco_annotations) + 1,
                "image_id": detection["frame"],
                "category_id": category_id,
                "track_id": int(track_id),
                "bbox": [left, top_y, right - left, bottom - top_y],
                "score": top[1],
            })
        dive_tracks[track_id] = {
            "begin": min(frames), "end": max(frames), "id": int(track_id),
            "features": [
                {"frame": d["frame"], "bounds": d["bounds"], "keyframe": True}
                for d in track["detections"]
            ],
            "confidencePairs": pairs,
            "attributes": {},
        }

    (root / "hierarchical.viame.csv").write_text("\n".join(rows) + "\n")
    (root / "hierarchical.tracks.json").write_text(
        json.dumps({"tracks": dive_tracks, "groups": {}, "version": 2}, indent=2) + "\n"
    )
    (root / "hierarchical.coco.json").write_text(json.dumps({
        "images": sorted(coco_images.values(), key=lambda i: i["id"]),
        "annotations": coco_annotations,
        "categories": [{"id": i, "name": n} for n, i in coco_categories.items()],
    }, indent=2) + "\n")


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
