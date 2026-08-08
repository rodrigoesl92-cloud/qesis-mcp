"""Minimal pure-stdlib reader for ESRI shapefiles and dBASE attribute tables.

Written because geopandas, fiona, pyshp and osgeo are all absent from this
runtime and the machine cannot afford the install (see qesis-compute-split:
generation runs local under roughly 450 MB of free RAM). Scope is deliberately
narrow: PolyLine geometry in a geographic CRS, which is every layer in the
EMODnet HA Telecommunication Cables release.

Reference: ESRI Shapefile Technical Description, July 1998.
"""

import struct
from math import radians, sin, cos, asin, sqrt

# Shape type codes we accept. Everything else is refused rather than guessed.
POLYLINE = 3
POLYLINE_Z = 13
POLYLINE_M = 23
_ACCEPTED = (POLYLINE, POLYLINE_Z, POLYLINE_M)


def read_shp(path):
    """Yield one list-of-parts per feature. Each part is a list of (lon, lat).

    Null shapes (type 0) yield an empty list so record indexing stays aligned
    with the .dbf, which is what lets attributes and geometry be zipped later.
    """
    with open(path, "rb") as fh:
        blob = fh.read()

    if struct.unpack(">i", blob[0:4])[0] != 9994:
        raise ValueError(f"{path}: not a shapefile (bad magic)")

    file_type = struct.unpack("<i", blob[32:36])[0]
    if file_type not in _ACCEPTED:
        raise ValueError(f"{path}: shape type {file_type} is not a PolyLine")

    out = []
    pos = 100  # main header is fixed at 100 bytes
    end = len(blob)
    while pos < end:
        # Record header is big-endian: record number, then content length in
        # 16-bit words.
        _, content_words = struct.unpack(">ii", blob[pos:pos + 8])
        pos += 8
        rec_end = pos + content_words * 2

        shape_type = struct.unpack("<i", blob[pos:pos + 4])[0]
        if shape_type == 0:  # null shape
            out.append([])
            pos = rec_end
            continue

        # bbox (4 doubles) then part count, point count
        n_parts, n_points = struct.unpack("<ii", blob[pos + 36:pos + 44])
        p = pos + 44
        part_starts = struct.unpack(f"<{n_parts}i", blob[p:p + 4 * n_parts])
        p += 4 * n_parts
        coords = struct.unpack(f"<{2 * n_points}d", blob[p:p + 16 * n_points])

        parts = []
        for i, start in enumerate(part_starts):
            stop = part_starts[i + 1] if i + 1 < n_parts else n_points
            parts.append([(coords[2 * j], coords[2 * j + 1])
                          for j in range(start, stop)])
        out.append(parts)
        pos = rec_end
    return out


def read_dbf(path):
    """Return a list of dicts, one per record, with deleted records dropped."""
    with open(path, "rb") as fh:
        blob = fh.read()

    n_records, header_len, record_len = struct.unpack("<ihh", blob[4:12])

    fields = []
    p = 32
    while blob[p] != 0x0D:  # 0x0D terminates the field descriptor array
        name = blob[p:p + 11].split(b"\x00")[0].decode("latin-1").strip()
        ftype = chr(blob[p + 11])
        flen = blob[p + 16]
        fields.append((name, ftype, flen))
        p += 32

    rows = []
    pos = header_len
    for _ in range(n_records):
        chunk = blob[pos:pos + record_len]
        pos += record_len
        if not chunk or chunk[0:1] == b"*":  # tombstone
            continue
        rec = {}
        off = 1  # first byte is the deletion flag
        for name, ftype, flen in fields:
            raw = chunk[off:off + flen]
            off += flen
            val = raw.decode("latin-1").strip()
            if ftype in "NF":
                try:
                    val = float(val) if val else None
                except ValueError:
                    val = None
            elif ftype == "L":
                val = val.upper() in ("Y", "T")
            rec[name] = val
        rows.append(rec)
    return rows


def haversine_km(a, b):
    """Great-circle distance between two (lon, lat) pairs, in kilometres."""
    lon1, lat1 = a
    lon2, lat2 = b
    dlon = radians(lon2 - lon1)
    dlat = radians(lat2 - lat1)
    h = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * 6371.0088 * asin(sqrt(min(1.0, h)))


def feature_length_km(parts):
    """Summed great-circle length of every part of one feature."""
    total = 0.0
    for part in parts:
        for i in range(len(part) - 1):
            total += haversine_km(part[i], part[i + 1])
    return total
