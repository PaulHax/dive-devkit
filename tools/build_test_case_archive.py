#!/usr/bin/env python3
"""Build a DIVE test-case archive from a checked-in set manifest.

The test-cases directory owns the long-lived case descriptions. A set manifest selects cases for
one archive. This builder adds generated media and synthetic JSON inputs. Generated output stays
ignored by Git.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import zipfile
from pathlib import Path

import gen_hierarchy_scenarios
import sefsc_seamap

KIT = Path(__file__).resolve().parents[1]
CASE_CATALOG = KIT / "test-cases"
DEFAULT_MANIFEST = CASE_CATALOG / "sets" / "hierarchical-classification.json"
GENERATED_ROOT = Path(os.environ.get("DIVE_DEVKIT_GENERATED") or KIT / ".generated")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n")


def copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def write_json(path: Path, payload: object) -> None:
    write_text(path, json.dumps(payload, indent=2))


def load_manifest(path: Path) -> dict:
    manifest = json.loads(path.read_text())
    if manifest.get("schemaVersion") != 1:
        raise SystemExit(f"unsupported test-case set schema: {path}")
    for key in ("id", "title", "archiveRoot", "outputName"):
        if not isinstance(manifest.get(key), str) or not manifest[key]:
            raise SystemExit(f"test-case set requires a non-empty {key}: {path}")
    for key in ("cases", "media"):
        if not isinstance(manifest.get(key), list) or not all(
            isinstance(value, str) and value for value in manifest[key]
        ):
            raise SystemExit(f"test-case set requires a string array for {key}: {path}")
    for relative in manifest["cases"]:
        case_path = Path(relative)
        if case_path.is_absolute() or ".." in case_path.parts:
            raise SystemExit(f"unsafe case path in {path}: {relative}")
        if not (CASE_CATALOG / case_path / "README.md").is_file():
            raise SystemExit(f"case not found in catalog: {relative}")
    return manifest


def warning_coco(track_id: int, category_name: str) -> dict:
    return {
        "images": [{"id": 1, "file_name": "hierarchy-frame-001.jpg", "frame_index": 0}],
        "annotations": [{
            "id": track_id,
            "image_id": 1,
            "category_id": 5,
            "bbox": [10, 20, 30, 40],
            "track_id": track_id,
            "iscrowd": 1,
            "segmentation": {"size": [100, 100], "counts": "abc"},
        }],
        "categories": [{"id": 5, "name": category_name}],
    }


def exact_confidence_pairs_kwcoco() -> dict:
    return {
        "info": {"dive_extensions": ["dive_confidence_pairs"]},
        "images": [
            {"id": 1, "file_name": "hierarchy-frame-001.jpg", "frame_index": 0},
            {"id": 8, "file_name": "hierarchy-frame-008.jpg", "frame_index": 7},
        ],
        "annotations": [
            {
                "id": 101,
                "image_id": 1,
                "category_id": 5,
                "track_id": 17,
                "bbox": [11, 21, 30, 40],
                "score": 0.9,
                "prob": [0.9, 0.1, 0],
                "dive_confidence_pairs": [["fish", 0.9], ["shark", 0.1]],
            },
            {
                "id": 100,
                "image_id": 8,
                "category_id": 7,
                "track_id": 17,
                "bbox": [10, 20, 30, 40],
                "score": 0.8,
                "prob": [0, 0.8, 0.2],
                "dive_confidence_pairs": [["shark", 0.8], ["fish", 0], ["rock", 0.2]],
            },
        ],
        "categories": [
            {"id": 5, "name": "fish"},
            {"id": 7, "name": "shark", "supercategory": "fish"},
            {"id": 11, "name": "rock"},
        ],
    }


def copy_baseline(scenario_root: Path, destination: Path) -> None:
    copy_file(
        scenario_root / "multipair-tracks.annotations.json",
        destination / "multipair.annotations.json",
    )
    copy_file(
        scenario_root / "valid-three-level-forest.config.json",
        destination / "three-level-forest.config.json",
    )


def copy_multicam_inputs(scenario_root: Path, destination: Path) -> None:
    source = scenario_root / "multicam"
    copy_file(source / "port-tracks.annotations.json", destination / "port.annotations.json")
    copy_file(source / "starboard-tracks.annotations.json", destination / "starboard.annotations.json")
    copy_file(
        scenario_root / "valid-three-level-forest.config.json",
        destination / "three-level-forest.config.json",
    )


def populate_case(
    relative: str,
    scenario_root: Path,
    output_dir: Path,
    force_media: bool,
) -> None:
    destination = output_dir / relative
    if relative == "classification/single-camera-linked-types":
        copy_file(
            scenario_root / "multipair-tracks.annotations.json",
            destination / "tracks.annotations.json",
        )
        copy_file(
            scenario_root / "valid-three-level-forest.config.json",
            destination / "type-hierarchy.config.json",
        )
    elif relative == "classification/multicamera-linked-types":
        annotations = scenario_root / "multipair-tracks.annotations.json"
        copy_file(annotations, destination / "port.annotations.json")
        copy_file(annotations, destination / "starboard.annotations.json")
        copy_file(
            scenario_root / "valid-three-level-forest.config.json",
            destination / "type-hierarchy.config.json",
        )
    elif relative == "classification/sefsc-seamap-fish-taxonomy":
        source = sefsc_seamap.generate(force=force_media)
        for name in (
            sefsc_seamap.VIDEO_NAME,
            "annotations.viame.csv",
            "config.json",
        ):
            copy_file(source / name, destination / name)
        copy_file(
            KIT / "seed" / "seamap-taxonomy.json",
            destination / "seamap-taxonomy.reference.json",
        )
    elif relative == "coco/rle-mask-warning-aggregation":
        write_json(destination / "rle-warning-fish.coco.json", warning_coco(1, "fish"))
        write_json(destination / "rle-warning-shark.coco.json", warning_coco(2, "shark"))
    elif relative == "clone/single-camera-metadata-isolation":
        copy_file(
            scenario_root / "multipair-tracks.annotations.json",
            destination / "source.annotations.json",
        )
        copy_file(
            scenario_root / "valid-three-level-forest.config.json",
            destination / "source.config.json",
        )
        replacement = {
            "typeHierarchy": {
                "juvenile-red-snapper": "red-snapper",
                "red-snapper": "fish",
            },
        }
        write_json(destination / "clone-replacement.config.json", replacement)
    elif relative == "hierarchy/valid-three-level-forest":
        copy_baseline(scenario_root, destination)
    elif relative == "hierarchy/invalid-configurations":
        for path in sorted(scenario_root.glob("*.config.json")):
            if path.name != "valid-three-level-forest.config.json":
                copy_file(path, destination / path.name)
    elif relative in {
        "multicamera/divergent-classification-replicas",
        "multicamera/disjoint-track-merge",
    }:
        copy_multicam_inputs(scenario_root, destination)
    elif relative == "kwcoco/exact-confidence-pairs-round-trip":
        write_json(destination / "exact-confidence-pairs.kwcoco.json", exact_confidence_pairs_kwcoco())
    elif relative == "kwcoco/empty-confidence-pairs-extension":
        copy_file(
            scenario_root / "empty-confidence-pairs.kwcoco.json",
            destination / "empty-confidence-pairs.kwcoco.json",
        )
    elif relative in {
        "display/resolved-attribute-filters",
        "display/resolved-suppression-regions",
        "export/raw-confidence-pair-filtering",
    }:
        copy_baseline(scenario_root, destination)
    else:
        raise SystemExit(f"case has no input generator: {relative}")


def write_checksums(output_dir: Path) -> None:
    rows = []
    for path in sorted(path for path in output_dir.rglob("*") if path.is_file()):
        if path.name == "SHA256SUMS":
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        rows.append(f"{digest}  {path.relative_to(output_dir).as_posix()}")
    write_text(output_dir / "SHA256SUMS", "\n".join(rows))


def write_zip(output_dir: Path, zip_path: Path, archive_root: str) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(path for path in output_dir.rglob("*") if path.is_file()):
            relative = path.relative_to(output_dir).as_posix()
            info = zipfile.ZipInfo(f"{archive_root}/{relative}", (2020, 1, 1, 0, 0, 0))
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED)


def build_archive(
    manifest_path: Path,
    output_dir: Path | None,
    zip_path: Path | None,
    force_media: bool = False,
) -> tuple[Path, Path]:
    manifest = load_manifest(manifest_path)
    scenario_root = gen_hierarchy_scenarios.generate(
        gen_hierarchy_scenarios.DEFAULT_ROOT,
        force_media,
    )
    if output_dir is None:
        output_dir = GENERATED_ROOT / "test-data" / manifest["outputName"]
    output_dir = output_dir.resolve()
    if output_dir == Path(output_dir.anchor) or len(output_dir.parts) < 4:
        raise SystemExit(f"refusing unsafe output directory: {output_dir}")
    if zip_path is None:
        zip_path = output_dir.with_suffix(".zip")
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    archive_readme = (
        f"# {manifest['title']} test data\n\n"
        "`MANIFEST.json` lists the long-lived test cases in this archive. Each case directory "
        "contains its condition, procedure, expected behavior, and generated inputs.\n"
    )
    write_text(output_dir / "README.md", archive_readme)
    write_json(output_dir / "MANIFEST.json", manifest)

    for relative in manifest["cases"]:
        shutil.copytree(CASE_CATALOG / relative, output_dir / relative)
        populate_case(relative, scenario_root, output_dir, force_media)

    media = set(manifest["media"])
    if "image-sequence" in media:
        shutil.copytree(scenario_root / "images", output_dir / "media" / "image-sequence")
    if "multicamera" in media:
        for camera in ("port", "starboard"):
            shutil.copytree(
                scenario_root / "multicam" / camera / "images",
                output_dir / "media" / "multicamera" / camera / "images",
            )
    unsupported_media = media - {"image-sequence", "multicamera"}
    if unsupported_media:
        raise SystemExit(f"unsupported media set: {', '.join(sorted(unsupported_media))}")

    for path in output_dir.rglob("*.json"):
        json.loads(path.read_text())
    write_checksums(output_dir)
    write_zip(output_dir, zip_path, manifest["archiveRoot"])
    return output_dir, zip_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--zip", dest="zip_path", type=Path)
    parser.add_argument("--force-media", action="store_true", help="re-cut the shared image files")
    args = parser.parse_args()
    output_dir, zip_path = build_archive(
        args.manifest,
        args.output_dir,
        args.zip_path,
        args.force_media,
    )
    print(f"test data directory: {output_dir}")
    print(f"test data archive:   {zip_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
