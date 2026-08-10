#!/usr/bin/env python3
"""Write a typeHierarchy straight into a dataset folder's Girder metadata, bypassing DIVE.

Every DIVE write path validates the hierarchy and rejects a malformed one, while the read path
returns stored metadata untouched so the viewer can report corruption. Planting through Girder's
generic folder-metadata endpoint is therefore the only way to exercise the viewer's
"Invalid Type Hierarchy" prompt (and any repair flow behind it).

  uv run --with girder-client --no-project python tools/plant_type_hierarchy.py <folderId> \
      .generated/hierarchical-classification/self-edge.config.json

Payloads come from tools/gen_hierarchy_scenarios.py (one per branch of the normalizer).

The payload is either a bare hierarchy or an object with a "typeHierarchy" key (the fixture shape).
Pass --clear to remove the key instead.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from girder_client import GirderClient


def payload_hierarchy(path: Path) -> object:
    data = json.loads(path.read_text())
    if isinstance(data, dict) and "typeHierarchy" in data:
        return data["typeHierarchy"]
    return data


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("folder_id")
    ap.add_argument("payload", nargs="?", type=Path, help="fixture JSON holding the hierarchy")
    ap.add_argument("--clear", action="store_true", help="delete typeHierarchy instead")
    ap.add_argument("--api-url", default="http://localhost:8010/api/v1")
    ap.add_argument("--user", default="admin")
    ap.add_argument("--password", default="letmein")
    ap.add_argument("--viewer-url", default="http://localhost:3000")
    args = ap.parse_args()

    if not args.clear and args.payload is None:
        ap.error("payload is required unless --clear is given")

    gc = GirderClient(apiUrl=args.api_url)
    gc.authenticate(username=args.user, password=args.password)

    if args.clear:
        gc.sendRestRequest(
            "DELETE",
            f"folder/{args.folder_id}/metadata",
            json=["typeHierarchy"],
        )
    else:
        hierarchy = payload_hierarchy(args.payload)
        # allowNull keeps an explicit null from being dropped by Girder's metadata merge.
        gc.sendRestRequest(
            "PUT",
            f"folder/{args.folder_id}/metadata",
            parameters={"allowNull": True},
            json={"typeHierarchy": hierarchy},
        )

    stored = gc.get(f"dive_dataset/{args.folder_id}").get("typeHierarchy")
    print(f"stored typeHierarchy: {json.dumps(stored)}")
    print(f"viewer: {args.viewer_url}/#/viewer/{args.folder_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
