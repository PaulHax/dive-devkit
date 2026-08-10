#!/usr/bin/env python3
"""Refresh the checked-in SEAMAP taxonomy from the public VIAME SEFSC-SEAMAP model.

Run this by hand when the add-on is republished; the seeder never calls it. Output is the static
JSON under seed/, which is what datasets actually reference.

The SEAMAP species classifier is a 2.4 GB add-on whose class list lives in a 120 KB
``train_info.json`` nested two zips deep. Both zips store that entry uncompressed, so this reads
the central directories and range-fetches only the one member -- roughly 0.006% of the archive.
Nothing is cached in the repo; the fetch is the source of truth and requires network access.

Class labels are ``GENUSSPECIES-<code>`` where the code is an NODC/ITIS taxonomic serial number.
Those codes are hierarchical by digit suffix -- CARANGIDAE is 170110000, the genus Caranx is
170110800, and Caranx crysos is 170110803 -- so a parent is the nearest ancestor code that is
itself a class. The model ships a hierarchy-capable graph with every edge list empty, so the
taxonomy is derived here, not copied.

Writes two files: the full 147-class hierarchy in the model's own vocabulary, and the same
taxonomy expressed in the annotation vocabulary of the FishTrack23 SEFSC clip, ready to drop into
a dataset config.

  python3 tools/derive_seamap_taxonomy.py
"""
from __future__ import annotations

import argparse
import json
import os
import re
import struct
import urllib.error
import urllib.request
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
SEED_DIR = KIT / "seed"

# VIAME add-on SEFSC-SEAMAP, from cmake/download_viame_addons.csv in the VIAME source tree.
# Public: no credentials. Pinned by file id so the class list cannot shift under us.
ADDON_URL = "https://viame.kitware.com/api/v1/file/69cea9e2dc8332f478b87605/download"
MEMBER = "configs/pipelines/models/seamap_species_enet2m_large.zip"
INNER_MEMBER_SUFFIX = "train_info.json"

LEVEL_WIDTHS = (2, 4)
LABEL_RE = re.compile(r"^(?P<name>[A-Z]+)-(?P<code>\d+)$")


# --------------------------------------------------------------------------- fetch


def _range(url: str, start: int, end: int) -> bytes:
    request = urllib.request.Request(url, headers={"Range": f"bytes={start}-{end}"})
    return urllib.request.urlopen(request, timeout=180).read()


def _content_length(url: str) -> int:
    request = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(request, timeout=60) as response:
        return int(response.headers["Content-Length"])


def _zip64(csize: int, usize: int, offset: int, extra: bytes) -> tuple[int, int, int]:
    """Replace 0xFFFFFFFF placeholders from the zip64 extended-information field."""
    if 0xFFFFFFFF not in (csize, usize, offset):
        return csize, usize, offset
    cursor = 0
    while cursor + 4 <= len(extra):
        header_id, size = struct.unpack("<HH", extra[cursor:cursor + 4])
        body = extra[cursor + 4:cursor + 4 + size]
        if header_id == 1:
            pos = 0
            if usize == 0xFFFFFFFF:
                usize = struct.unpack("<Q", body[pos:pos + 8])[0]
                pos += 8
            if csize == 0xFFFFFFFF:
                csize = struct.unpack("<Q", body[pos:pos + 8])[0]
                pos += 8
            if offset == 0xFFFFFFFF:
                offset = struct.unpack("<Q", body[pos:pos + 8])[0]
        cursor += 4 + size
    return csize, usize, offset


def _central_directory(url: str, base: int, size: int) -> list[dict]:
    """Parse the central directory of a zip whose bytes start at `base` and run `size` long."""
    end = base + size - 1
    tail = _range(url, max(base, end - 100_000), end)
    marker = tail.rfind(b"PK\x05\x06")
    if marker < 0:
        raise SystemExit("not a zip: no end-of-central-directory record")
    cd_size, cd_offset = struct.unpack("<II", tail[marker + 12:marker + 20])
    if 0xFFFFFFFF in (cd_size, cd_offset):
        zip64 = tail.rfind(b"PK\x06\x06")
        cd_size, cd_offset = struct.unpack("<QQ", tail[zip64 + 40:zip64 + 56])
    raw = _range(url, base + cd_offset, base + cd_offset + cd_size - 1)

    members, cursor = [], 0
    while cursor < len(raw) and raw[cursor:cursor + 4] == b"PK\x01\x02":
        fields = struct.unpack("<IHHHHHHIIIHHHHHII", raw[cursor:cursor + 46])
        method, csize, usize = fields[4], fields[8], fields[9]
        name_len, extra_len, comment_len, offset = fields[10], fields[11], fields[12], fields[16]
        name = raw[cursor + 46:cursor + 46 + name_len].decode("utf-8", "replace")
        extra = raw[cursor + 46 + name_len:cursor + 46 + name_len + extra_len]
        csize, usize, offset = _zip64(csize, usize, offset, extra)
        members.append({"name": name, "method": method, "csize": csize, "offset": offset})
        cursor += 46 + name_len + extra_len + comment_len
    return members


def _member_bytes(url: str, base: int, member: dict) -> tuple[int, int]:
    """Absolute byte range of a member's payload. Only stored (method 0) members are readable."""
    header = _range(url, base + member["offset"], base + member["offset"] + 300)
    name_len, extra_len = struct.unpack("<HH", header[26:30])
    start = base + member["offset"] + 30 + name_len + extra_len
    return start, start + member["csize"] - 1


def fetch_class_list() -> list[str]:
    """Range-read the class list out of the add-on. Fails loudly when offline."""
    try:
        size = _content_length(ADDON_URL)
        outer = _central_directory(ADDON_URL, 0, size)
        model = next((m for m in outer if m["name"] == MEMBER), None)
        if model is None:
            raise SystemExit(f"{MEMBER} is no longer in the add-on")
        if model["method"] != 0:
            raise SystemExit(f"{MEMBER} is compressed; cannot range-read the nested zip")
        base, _ = _member_bytes(ADDON_URL, 0, model)

        inner = _central_directory(ADDON_URL, base, model["csize"])
        info = next((m for m in inner if m["name"].endswith(INNER_MEMBER_SUFFIX)), None)
        if info is None:
            raise SystemExit(f"no {INNER_MEMBER_SUFFIX} inside {MEMBER}")
        if info["method"] != 0:
            raise SystemExit(f"{INNER_MEMBER_SUFFIX} is compressed; expected stored")
        start, end = _member_bytes(ADDON_URL, base, info)
        payload = json.loads(_range(ADDON_URL, start, end))
    except urllib.error.URLError as exc:
        raise SystemExit(f"cannot reach {ADDON_URL}: {exc.reason}") from exc

    classes = payload["hyper"]["model"][1]["classes"]["idx_to_node"]
    if not classes:
        raise SystemExit("class list is empty")
    return list(classes)


# --------------------------------------------------------------------- taxonomy


def _trailing_zeros(code: str) -> int:
    return len(code) - len(code.rstrip("0"))


def build_hierarchy(labels: list[str]) -> dict[str, str]:
    """Map each label to its nearest ancestor by taxonomic code.

    The codes are positional: a genus zeroes the last two digits of its species, a family the last
    four. Truncating past a level boundary crosses into an unrelated branch -- zeroing five digits
    off Bodianus pulchellus lands on Sciaenidae, which is a different family entirely -- so only
    the two real level widths are candidates, and a parent must sit at a coarser level than its
    child.
    """
    by_code = {}
    for label in labels:
        match = LABEL_RE.match(label)
        if match:
            by_code[match.group("code")] = label

    hierarchy = {}
    for code, label in by_code.items():
        depth = _trailing_zeros(code)
        for width in (w for w in LEVEL_WIDTHS if w > depth):
            candidate = code[:len(code) - width] + "0" * width
            if candidate in by_code:
                hierarchy[label] = by_code[candidate]
                break
    return hierarchy


def branch_of(label: str, hierarchy: dict[str, str]) -> list[str]:
    """Label first, then each ancestor up to the root."""
    chain, seen = [label], {label}
    while chain[-1] in hierarchy:
        parent = hierarchy[chain[-1]]
        if parent in seen:
            break
        chain.append(parent)
        seen.add(parent)
    return chain




# The eight labels the FishTrack23 SEFSC clip actually uses, in its own vocabulary.
SEFSC_LABELS = [
    "bodianus_pulchellus",
    "canthigaster_rostratus",
    "chaetodon_sedentarius",
    "epinephelus_morio",
    "holacanthus_bermudensis",
    "mycteroperca_phenax",
    "pterois",
    "seriola_rivoliana",
]


def readable(label: str) -> str:
    """Strip the taxonomic code and lowercase: CARANGIDAE-170110000 -> carangidae."""
    match = LABEL_RE.match(label)
    return (match.group("name") if match else label).lower()


def match_label(annotation_label: str, labels: list[str]) -> str | None:
    """Find the model class for an annotation label.

    Species endings disagree between the two vocabularies -- the clip says
    ``canthigaster_rostratus`` where the model says ``CANTHIGASTERROSTRATA`` -- so the genus must
    match exactly and the species only by prefix.
    """
    parts = annotation_label.upper().split("_")
    genus, species = parts[0], "".join(parts[1:])
    candidates = [l for l in labels if LABEL_RE.match(l) and readable(l).upper().startswith(genus)]
    if not candidates:
        return None
    if not species:
        exact = [l for l in candidates if readable(l).upper() == genus]
        return exact[0] if exact else min(candidates, key=lambda l: len(readable(l)))
    for length in range(len(species), 3, -1):
        for candidate in candidates:
            rest = readable(candidate).upper()[len(genus):]
            if rest.startswith(species[:length]):
                return candidate
    return None


def sefsc_hierarchy(labels: list[str], hierarchy: dict[str, str]) -> dict[str, str]:
    """Express the derived taxonomy in the clip's annotation vocabulary."""
    out = {}
    for annotation_label in SEFSC_LABELS:
        matched = match_label(annotation_label, labels)
        if matched is None:
            raise SystemExit(f"no SEAMAP class matches {annotation_label}")
        chain = [annotation_label] + [readable(a) for a in branch_of(matched, hierarchy)[1:]]
        for child, parent in zip(chain, chain[1:]):
            out[child] = parent
    return out


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    labels = fetch_class_list()
    hierarchy = build_hierarchy(labels)
    SEED_DIR.mkdir(parents=True, exist_ok=True)

    full = {
        "_comment": (
            "Derived by tools/derive_seamap_taxonomy.py from the public VIAME SEFSC-SEAMAP "
            "add-on's class list. Parents come from the taxonomic codes in the class labels; "
            "the model's own graph ships with no edges. Regenerate rather than hand-edit."
        ),
        "source": ADDON_URL,
        "classCount": len(labels),
        "typeHierarchy": dict(sorted(hierarchy.items())),
    }
    (SEED_DIR / "seamap-taxonomy.json").write_text(json.dumps(full, indent=2) + "\n")

    clip = {
        "_comment": (
            "The same taxonomy in the annotation vocabulary of the FishTrack23 SEFSC clip, so it "
            "can be dropped straight into that dataset's config as typeHierarchy."
        ),
        "typeHierarchy": dict(sorted(sefsc_hierarchy(labels, hierarchy).items())),
    }
    (SEED_DIR / "sefsc-seamap-hierarchy.json").write_text(json.dumps(clip, indent=2) + "\n")

    depths = [len(branch_of(l, hierarchy)) for l in labels]
    print(f"seed/seamap-taxonomy.json         {len(labels)} classes, {len(hierarchy)} links, "
          f"max depth {max(depths)}")
    print(f"seed/sefsc-seamap-hierarchy.json  {len(clip['typeHierarchy'])} links "
          f"over {len(SEFSC_LABELS)} annotated types")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
