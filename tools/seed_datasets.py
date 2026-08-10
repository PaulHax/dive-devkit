#!/usr/bin/env python3
"""Seed a local DIVE/Girder stack with a known set of datasets (consistent test surface).

Idempotent: a dataset that already exists (by name, under the Seed folder) is left alone
unless --force. Self-verifies expectedTrackCount / expectedFrameMetadataSources
(exit 1 on any mismatch/failure).

Every entry names a "generate" script that builds its own media and data under .generated/
(DIVE_DEVKIT_GENERATED) and needs nothing else -- the kit reads no external media library, so a
fresh clone can seed a stack with only ffmpeg and network access.

Run with girder_client available:
  uv run --with girder-client --no-project python tools/seed_datasets.py
"""
from __future__ import annotations

import argparse
import binascii
import json
import os
import sys
import time
import zlib
from pathlib import Path

from girder_client import GirderClient

import gen_hierarchy_scenarios
import okeanos_media
import sefsc_seamap

KIT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = KIT / "seed" / "seed.json"
GENERATED_ROOT = Path(os.environ.get("DIVE_DEVKIT_GENERATED") or KIT / ".generated")

# queued/running job statuses (girder + girder_worker); see DIVE integration conftest.wait_for_jobs
INCOMPLETE_JOB_STATUSES = [0, 1, 2, 820, 821, 822, 823, 824]


def connect(api_url: str, user: str, password: str) -> GirderClient:
    gc = GirderClient(apiUrl=api_url)
    gc.authenticate(username=user, password=password)
    return gc


def seed_folder(gc: GirderClient) -> dict:
    me = gc.get("user/me")
    return gc.loadOrCreateFolder("Seed", me["_id"], "user")


def find_dataset(gc: GirderClient, parent_id: str, name: str) -> dict | None:
    return next(iter(gc.listFolder(parent_id, name=name)), None)


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    payload = kind + data
    return (
        len(data).to_bytes(4, "big")
        + payload
        + binascii.crc32(payload).to_bytes(4, "big")
    )


def write_png(path: Path, rgb: tuple[int, int, int], width: int = 64, height: int = 48) -> None:
    """Write a tiny RGB PNG using only the standard library."""
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = b"".join(b"\x00" + bytes(rgb) * width for _ in range(height))
    ihdr = (
        width.to_bytes(4, "big")
        + height.to_bytes(4, "big")
        + b"\x08\x02\x00\x00\x00"
    )
    data = (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", zlib.compress(raw))
        + _png_chunk(b"IEND", b"")
    )
    path.write_bytes(data)


def generate_multicam_frame_metadata_fixture() -> None:
    """Create a small stereo image-sequence fixture with local and shared sidecars."""
    root = GENERATED_ROOT / "multicam-frame-metadata"
    frames = range(4)
    cameras = {
        "port": {
            "color": (24, 64, 128),
            "prefix": "port",
            "column": "port_image",
            "local_column": "port_local_note",
        },
        "starboard": {
            "color": (128, 64, 24),
            "prefix": "starboard",
            "column": "starboard_image",
            "local_column": "starboard_local_note",
        },
    }
    for camera, spec in cameras.items():
        image_dir = root / camera / "images"
        sidecar_dir = root / camera / "sidecar"
        image_dir.mkdir(parents=True, exist_ok=True)
        sidecar_dir.mkdir(parents=True, exist_ok=True)
        rows = ["filename,local_depth_m,local_note"]
        for frame in frames:
            filename = f"{spec['prefix']}_frame_{frame:03d}.png"
            write_png(image_dir / filename, spec["color"])
            rows.append(f"{filename},{100 + frame},{spec['local_column']}_{frame}")
        (sidecar_dir / "frame_metadata.csv").write_text("\n".join(rows) + "\n")

    shared_rows = ["port_image,starboard_image,vehicle_altitude_m,shared_note"]
    for frame in frames:
        shared_rows.append(
            ",".join(
                [
                    f"port_frame_{frame:03d}.png",
                    f"starboard_frame_{frame:03d}.png",
                    str(20 + frame),
                    f"shared_frame_{frame}",
                ]
            )
        )
    shared_dir = root / "shared"
    shared_dir.mkdir(parents=True, exist_ok=True)
    (shared_dir / "frame-metadata.csv").write_text("\n".join(shared_rows) + "\n")


def ensure_generated_fixture(entry: dict) -> None:
    if entry.get("generate") == "sefsc-seamap":
        sefsc_seamap.generate()
    if entry.get("generate") == "okeanos-media":
        okeanos_media.generate()
    if entry.get("generate") == "multicam-frame-metadata":
        generate_multicam_frame_metadata_fixture()
    if entry.get("generate") == "hierarchical-classification":
        gen_hierarchy_scenarios.generate(GENERATED_ROOT / "hierarchical-classification")


def _file_specs(entry: dict, key: str) -> list[dict]:
    specs = []
    for value in entry.get(key, []):
        if isinstance(value, str):
            specs.append({"path": value})
        else:
            specs.append(value)
    return specs


def _spec_path(spec: dict) -> Path:
    return GENERATED_ROOT / spec["path"]


def _entry_paths(entry: dict, key: str) -> list[Path]:
    return [_spec_path(spec) for spec in _file_specs(entry, key)]


def plant_path(entry: dict) -> Path | None:
    """Resolve the hierarchy payload an entry plants, if any (same spec shape as media paths)."""
    plant = entry.get("plantTypeHierarchy")
    if plant is None:
        return None
    return _spec_path({"path": plant} if isinstance(plant, str) else plant)


def _all_upload_entries(entry: dict) -> list[dict]:
    entries = [entry]
    entries.extend((entry.get("cameras") or {}).values())
    return entries


def verify_media(entry: dict) -> list[str]:
    """Return problems (missing file / empty dir); empty == ok."""
    problems = []
    plant = plant_path(entry)
    if plant and not plant.exists():
        problems.append(f"missing: {plant}")
    for upload_entry in _all_upload_entries(entry):
        for path in (
            _entry_paths(upload_entry, "media")
            + _entry_paths(upload_entry, "frameMetadata")
            + _entry_paths(upload_entry, "data")
        ):
            if not path.exists():
                problems.append(f"missing: {path}")
            elif path.is_dir():
                if not any(f.is_file() for f in path.iterdir()):
                    problems.append(f"empty dir: {path}")
    return problems


def _resolve_specs(specs: list[dict]) -> list[tuple[Path, str | None]]:
    resolved: list[tuple[Path, str | None]] = []
    for spec in specs:
        path = _spec_path(spec)
        upload_name = spec.get("name")
        if path.is_dir():
            resolved.extend((f, None) for f in sorted(
                f for f in path.iterdir() if f.is_file() and not f.name.startswith(".")
            ))
        else:
            resolved.append((path, upload_name))
    return resolved


def resolved_paths(entry: dict, key: str) -> list[tuple[Path, str | None]]:
    """Resolve an entry's declared paths for one key to a flat file list; a directory expands to
    its files (image sequences), a file passes through."""
    return _resolve_specs(_file_specs(entry, key))


def postprocess(gc: GirderClient, folder_id: str, attempts: int = 4) -> list[str]:
    """POST postprocess, retrying transient 5xx (girder/mongo cold-start race right after `up`)."""
    for i in range(attempts):
        try:
            response = gc.post(f"dive_rpc/postprocess/{folder_id}", data={"skipJobs": False})
            return response.get("job_ids", []) if isinstance(response, dict) else []
        except Exception as e:  # noqa: BLE001
            transient = any(c in str(e) for c in ("500", "502", "503", "OperationalError"))
            if i == attempts - 1 or not transient:
                raise
            time.sleep(3)
    return []


def wait_for_jobs(gc: GirderClient, job_ids: list[str], timeout: int) -> bool:
    if not job_ids:
        return True
    start = time.time()
    while time.time() - start < timeout:
        jobs = [gc.get(f"job/{job_id}") for job_id in job_ids]
        if all(job.get("status") not in INCOMPLETE_JOB_STATUSES for job in jobs):
            return True
        time.sleep(2)
    return False


def track_count(gc: GirderClient, folder_id: str) -> int | None:
    try:
        return len(gc.get("dive_annotation/track", parameters={"folderId": folder_id, "limit": 0}))
    except Exception:  # noqa: BLE001
        return None


def frame_metadata_source_counts(gc: GirderClient, folder_id: str) -> tuple[int, int] | None:
    """Count selected frame-metadata attachments in the server listing.

    The response has one optional shared attachment and at most one attachment per camera.
    Counting those selected scopes confirms the attachments survived import and are discoverable;
    the row-to-frame join itself runs client-side and is not checked here.
    """
    try:
        response = gc.get(f"dive_dataset/{folder_id}/frame_metadata_sources")
    except Exception:  # noqa: BLE001
        return None
    cameras = response.get("cameras") or {}
    attachments = [response.get("shared"), *cameras.values()]
    selected = [
        attachment
        for attachment in attachments
        if isinstance(attachment, dict) and attachment.get("itemId")
    ]
    unique_item_ids = set()
    for attachment in selected:
        unique_item_ids.add(attachment["itemId"])
    return len(selected), len(unique_item_ids)


def frame_metadata_source_count(gc: GirderClient, folder_id: str) -> int | None:
    counts = frame_metadata_source_counts(gc, folder_id)
    return None if counts is None else counts[0]


def upload_entry_files(gc: GirderClient, folder_id: str, entry: dict) -> None:
    for key in ("media", "frameMetadata", "data"):
        for path, upload_name in resolved_paths(entry, key):
            gc.uploadFileToFolder(folder_id, str(path), filename=upload_name)


def seed_multicam(
    gc: GirderClient,
    parent_id: str,
    entry: dict,
    force: bool,
) -> dict:
    name = entry["name"]
    existing = find_dataset(gc, parent_id, name)
    if existing and not force:
        return {"name": name, "id": existing["_id"], "status": "exists"}

    try:
        parent = gc.createFolder(
            parent_id,
            name,
            reuseExisting=True,
            description="Multicamera dataset",
        )
        upload_entry_files(gc, parent["_id"], entry)

        camera_ids = {}
        camera_order = entry.get("cameraOrder") or list((entry.get("cameras") or {}).keys())
        for camera_name in camera_order:
            camera_entry = entry["cameras"][camera_name]
            folder = gc.createFolder(
                parent["_id"],
                camera_name,
                reuseExisting=True,
                metadata={"fps": entry["fps"], "type": entry["type"]},
            )
            upload_entry_files(gc, folder["_id"], camera_entry)
            job_ids = postprocess(gc, folder["_id"])
            if not wait_for_jobs(gc, job_ids, entry.get("jobTimeout", 120)):
                return {
                    "name": name,
                    "status": "failed",
                    "problems": [f"jobs still running for camera {camera_name}"],
                }
            camera_ids[camera_name] = {"folderId": folder["_id"]}

        parent = gc.sendRestRequest(
            "POST",
            "/dive_dataset/multicam",
            parameters={"parentFolderId": parent["_id"]},
            json={
                "name": name,
                "fps": entry["fps"],
                "type": entry["type"],
                "subType": entry.get("subType", "multicam"),
                "defaultDisplay": entry["defaultDisplay"],
                "cameraOrder": camera_order,
                "cameras": camera_ids,
            },
        )
    except Exception as e:  # noqa: BLE001
        return {"name": name, "status": "failed", "problems": [str(e)[:160]]}
    return {"name": name, "id": parent["_id"], "status": "created"}


def plant_type_hierarchy(gc: GirderClient, folder_id: str, payload: Path) -> object:
    """Write a hierarchy through Girder's generic metadata endpoint, bypassing DIVE validation.

    DIVE rejects a malformed hierarchy on every write path but returns stored metadata untouched on
    read, so planting is the only way to seed the corrupt state the viewer warns about.
    """
    data = json.loads(payload.read_text())
    hierarchy = data["typeHierarchy"] if isinstance(data, dict) and "typeHierarchy" in data else data
    gc.sendRestRequest(
        "PUT",
        f"folder/{folder_id}/metadata",
        parameters={"allowNull": True},
        json={"typeHierarchy": hierarchy},
    )
    return hierarchy


def seed_one(gc: GirderClient, parent_id: str, entry: dict, force: bool) -> dict:
    name = entry["name"]
    ensure_generated_fixture(entry)
    existing = find_dataset(gc, parent_id, name)
    if existing and not force:
        return {"name": name, "id": existing["_id"], "status": "exists"}

    problems = verify_media(entry)
    if problems:
        return {"name": name, "status": "skipped", "problems": problems}

    if "cameras" in entry:
        return seed_multicam(gc, parent_id, entry, force)

    try:
        folder = gc.createFolder(
            parent_id, name, reuseExisting=True,
            metadata={"fps": entry["fps"], "type": entry["type"]},
        )
        upload_entry_files(gc, folder["_id"], entry)
        # skipJobs=False so DIVE marks the folder a dataset (DatasetMarker is only set on this
        # path) and transcodes any media that needs it; websafe image sequences launch no job.
        job_ids = postprocess(gc, folder["_id"])
        plant = plant_path(entry)
        if plant:
            plant_type_hierarchy(gc, folder["_id"], plant)
    except Exception as e:  # noqa: BLE001 — report per-dataset, keep seeding the rest
        return {"name": name, "status": "failed", "problems": [str(e)[:160]]}
    return {"name": name, "id": folder["_id"], "status": "created", "job_ids": job_ids}


def hierarchy_surface(gc: GirderClient, folder_id: str) -> tuple[dict, int] | None:
    """Return the persisted hierarchy and count of tracks carrying multiple type pairs."""
    try:
        meta = gc.get(f"dive_dataset/{folder_id}")
        tracks = gc.get(
            "dive_annotation/track",
            parameters={"folderId": folder_id, "limit": 0},
        )
    except Exception:  # noqa: BLE001
        return None
    multipair_count = sum(len(track.get("confidencePairs", [])) > 1 for track in tracks)
    return meta.get("typeHierarchy") or {}, multipair_count


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--api-url", default="http://localhost:8010/api/v1")
    ap.add_argument("--user", default="admin")
    ap.add_argument("--password", default="letmein")
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    ap.add_argument("--viewer-url", default="http://localhost:3000")
    ap.add_argument("--only", help="seed only datasets whose name contains this substring")
    ap.add_argument("--force", action="store_true", help="re-upload even if dataset exists")
    ap.add_argument("--job-timeout", type=int, default=300)  # 2 video transcodes on one cpu worker
    args = ap.parse_args()

    manifest = json.loads(args.manifest.read_text())
    entries = manifest["datasets"]
    if args.only:
        entries = [e for e in entries if args.only.lower() in e["name"].lower()]
    if not entries:
        print("no datasets matched", file=sys.stderr)
        return 1

    gc = connect(args.api_url, args.user, args.password)
    parent = seed_folder(gc)
    print(f"seeding {len(entries)} dataset(s) into Seed/ from {GENERATED_ROOT} ({args.api_url})")

    results = [seed_one(gc, parent["_id"], e, args.force) for e in entries]
    job_ids = [job_id for r in results for job_id in r.get("job_ids", [])]
    if job_ids:
        print(f"waiting for {len(job_ids)} transcode/convert job(s)…")
        if not wait_for_jobs(gc, job_ids, args.job_timeout):
            print("WARNING: jobs still running after timeout", file=sys.stderr)

    by_name = {e["name"]: e for e in entries}
    sidecar = args.manifest.parent / "seeded-local.json"
    record = {}
    ok = True
    print("\n  status    dataset                              id / problem")
    print("  " + "-" * 70)
    for r in results:
        if r["status"] in ("skipped", "failed"):
            ok = False
            print(f"  {r['status']:9} {r['name'][:34]:34}  {'; '.join(r['problems'])}")
            continue
        ds_id = r["id"]
        record[r["name"]] = {"id": ds_id, "viewer": f"{args.viewer_url}/#/viewer/{ds_id}"}
        note = ""
        expected = by_name.get(r["name"], {}).get("expectedTrackCount")
        if expected is not None:
            actual = track_count(gc, ds_id)
            record[r["name"]]["tracks"] = actual
            verdict = "OK" if actual == expected else "MISMATCH"
            ok = ok and actual == expected
            note += f"  tracks={actual}/{expected} {verdict}"
        expected_sources = by_name.get(r["name"], {}).get("expectedFrameMetadataSources")
        if expected_sources is not None:
            counts = frame_metadata_source_counts(gc, ds_id)
            actual = None if counts is None else counts[0]
            record[r["name"]]["frameMetadataSources"] = actual
            verdict = "OK" if actual == expected_sources else "MISMATCH"
            ok = ok and actual == expected_sources
            note += f"  frame_metadata_sources={actual}/{expected_sources} {verdict}"
            expected_unique = by_name.get(r["name"], {}).get("expectedFrameMetadataUniqueSources")
            if expected_unique is not None:
                unique_actual = None if counts is None else counts[1]
                record[r["name"]]["frameMetadataUniqueSources"] = unique_actual
                verdict = "OK" if unique_actual == expected_unique else "MISMATCH"
                ok = ok and unique_actual == expected_unique
                note += f"  unique_frame_metadata={unique_actual}/{expected_unique} {verdict}"
        expected_hierarchy = by_name.get(r["name"], {}).get("expectedTypeHierarchy")
        if expected_hierarchy is not None:
            surface = hierarchy_surface(gc, ds_id)
            actual_hierarchy = None if surface is None else surface[0]
            actual_multipair = None if surface is None else surface[1]
            expected_multipair = by_name[r["name"]].get("expectedMultipairTracks", 0)
            record[r["name"]]["typeHierarchy"] = actual_hierarchy
            record[r["name"]]["multipairTracks"] = actual_multipair
            matches = (
                actual_hierarchy == expected_hierarchy
                and actual_multipair == expected_multipair
            )
            verdict = "OK" if matches else "MISMATCH"
            ok = ok and matches
            note += f"  hierarchy_surface={verdict}"
        planted = plant_path(by_name.get(r["name"], {}))
        if planted is not None:
            expected_planted = json.loads(planted.read_text())["typeHierarchy"]
            actual_planted = gc.get(f"dive_dataset/{ds_id}").get("typeHierarchy")
            record[r["name"]]["typeHierarchy"] = actual_planted
            # The read path must hand the malformed value to the viewer verbatim, or the
            # "Invalid Type Hierarchy" prompt never fires.
            matches = actual_planted == expected_planted
            ok = ok and matches
            note += f"  planted_hierarchy={'OK' if matches else 'MISMATCH'}"
        print(f"  {r['status']:9} {r['name'][:34]:34}  {ds_id}{note}")
    sidecar.write_text(json.dumps(record, indent=2) + "\n")
    print(f"\nwrote {sidecar}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
