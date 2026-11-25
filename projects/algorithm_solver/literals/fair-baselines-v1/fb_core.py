"""Records, the archive container, and byte accounting shared by every baseline.

Byte accounting has one form for every method. Each archive byte is put in exactly one of
five categories, and the categories must sum to the serialized archive length:

  header   the fixed 16-byte container header (plus the part table of a partitioned archive)
  model    dictionary or symbol table stored in the archive
  index    the per-record (and per-block) offset table
  framing  bytes of a stored unit that are container format, not compressed content
           (zstd magic, frame header, block headers, checksum; the stored-raw flag bitmap)
  payload  everything else in the stored units
"""
from __future__ import annotations

import base64
import hashlib
import json
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

MAGIC = b'FBA1'
HEADER_BYTES = 16

M_RAW = 0
M_ZSTD_FRAME = 1
M_ZSTD_LEAN_FRAME = 2
M_ZSTD_BLOCK = 3
M_DEFLATE = 4
M_FSST = 5
M_ZSTD_LEAN_GROUP = 6
M_PARTITIONED = 7
M_LANE_FSST = 8   # the lane's own FSST-255 format; Python reader only

MODEL_NONE = 0
MODEL_ZSTD_DICT = 1
MODEL_ZSTD_RAW = 2
MODEL_DEFLATE_DICT = 3
MODEL_FSST_TABLE = 4
MODEL_LANE_FSST_TABLE = 5

LANE_HEADER_BYTES = 10   # the lane's ZST3 / DFL3 containers: 4-byte tag, u32 model length, u16 count
LANE_INDEX_WIDTH = 4


# ---------------------------------------------------------------- records

@dataclass
class RecordSet:
    records: list[bytes]
    groups: list[str] | None = None   # optional per-record group label
    source_kind: str = ''

    def __len__(self) -> int:
        return len(self.records)

    @property
    def total_bytes(self) -> int:
        return sum(len(r) for r in self.records)

    def sha256(self) -> str:
        h = hashlib.sha256()
        for r in self.records:
            h.update(struct.pack('<Q', len(r)))
            h.update(r)
        return h.hexdigest()

    def describe(self) -> dict:
        n = len(self.records)
        lens = sorted(len(r) for r in self.records)
        out = {
            'records': n,
            'total_bytes': self.total_bytes,
            'mean_record_bytes': round(self.total_bytes / n, 2) if n else 0,
            'min_record_bytes': lens[0] if n else 0,
            'median_record_bytes': lens[n // 2] if n else 0,
            'max_record_bytes': lens[-1] if n else 0,
            'sha256_of_length_prefixed_records': self.sha256(),
            'source_kind': self.source_kind,
        }
        if self.groups is not None:
            counts: dict[str, int] = {}
            for g in self.groups:
                counts[g] = counts.get(g, 0) + 1
            out['group_counts'] = counts
        return out


def _load_dir(path: Path) -> RecordSet:
    files = sorted((p for p in path.rglob('*') if p.is_file() and not p.name.startswith('.')),
                   key=lambda p: p.relative_to(path).as_posix())
    records, groups = [], []
    for p in files:
        rel = p.relative_to(path)
        records.append(p.read_bytes())
        groups.append(rel.parts[0] if len(rel.parts) > 1 else '')
    return RecordSet(records, groups if any(groups) else None, 'directory')


def _load_jsonl(path: Path) -> RecordSet:
    records, groups = [], []
    with path.open('r', encoding='utf-8') as fh:
        for ln, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            group = ''
            if isinstance(obj, str):
                rec = obj.encode('utf-8')
            elif isinstance(obj, dict):
                group = str(obj.get('group', ''))
                b64 = obj.get('base64', obj.get('b64'))
                txt = obj.get('text', obj.get('utf8'))
                if (b64 is None) == (txt is None):
                    raise ValueError(f'{path.name}:{ln}: need exactly one of "base64" or "text"')
                rec = base64.b64decode(b64, validate=True) if b64 is not None else str(txt).encode('utf-8')
            else:
                raise ValueError(f'{path.name}:{ln}: each line must be a JSON string or object')
            records.append(rec)
            groups.append(group)
    return RecordSet(records, groups if any(groups) else None, 'jsonl')


def load_records(path: str | Path) -> RecordSet:
    """A directory (one record per file, sorted by relative path; a first-level subdirectory name
    is the record's group) or a JSONL file (a JSON string, or an object with "text" or "base64"
    and an optional "group")."""
    p = Path(path)
    if p.is_dir():
        rs = _load_dir(p)
    elif p.is_file():
        rs = _load_jsonl(p)
    else:
        raise FileNotFoundError(f'no such record input: {p.name}')
    if not rs.records:
        raise ValueError(f'no records found in {p.name}')
    return rs


# ---------------------------------------------------------------- accounting

@dataclass
class Accounting:
    header: int = 0
    model: int = 0
    index: int = 0
    framing: int = 0
    payload: int = 0

    @property
    def total(self) -> int:
        return self.header + self.model + self.index + self.framing + self.payload

    def as_dict(self) -> dict:
        return {'header': self.header, 'model': self.model, 'index': self.index, 'framing': self.framing,
                'payload': self.payload, 'total': self.total}

    def __add__(self, other: 'Accounting') -> 'Accounting':
        return Accounting(self.header + other.header, self.model + other.model, self.index + other.index,
                          self.framing + other.framing, self.payload + other.payload)


def min_width(max_value: int) -> int:
    w = 1
    while max_value >= (1 << (8 * w)):
        w += 1
    return w


def _pack_offsets(ends: Sequence[int], width: int) -> bytes:
    if width == 4:
        return struct.pack(f'<{len(ends)}I', *ends)
    return b''.join(int(e).to_bytes(width, 'little') for e in ends)


@dataclass
class EncodedUnits:
    """What a codec produced for a set of records, before the index representation is chosen."""
    method: int
    model_kind: int
    model: bytes
    units: list[bytes]                 # stored units, in record (or block) order
    unit_framing: list[int]            # measured framing bytes inside each stored unit
    n_records: int
    per_block: int = 1
    rec_raw_ends: list[int] | None = None   # block method: cumulative raw end offset of every record
    aux: bytes = b''                   # stored-raw flag bitmap (raw zstd block method)
    detail: dict = field(default_factory=dict)
    parts: list['EncodedUnits'] | None = None   # partitioned archive

    def _max_offset(self) -> int:
        m = sum(len(u) for u in self.units)
        if self.rec_raw_ends:
            m = max(m, self.rec_raw_ends[-1])
        return m

    def pack(self, index_width: int | None = LANE_INDEX_WIDTH) -> tuple[bytes, Accounting]:
        """Serialize. index_width None means the smallest whole-byte width that holds every offset."""
        if self.parts is not None:
            return self._pack_partitioned(index_width)
        width = index_width if index_width is not None else min_width(self._max_offset())
        if self._max_offset() >= (1 << (8 * width)):
            raise ValueError(f'offsets do not fit in {width} index bytes')
        if not 0 < self.per_block < 256:
            raise ValueError('records per block must be 1..255')
        ends, cur = [], 0
        for u in self.units:
            cur += len(u)
            ends.append(cur)
        index = _pack_offsets(ends, width)
        if self.rec_raw_ends is not None:
            index += _pack_offsets(self.rec_raw_ends, width)
        header = MAGIC + bytes([self.method, width, self.model_kind, self.per_block]) + struct.pack(
            '<II', self.n_records, len(self.model))
        body = b''.join(self.units)
        archive = header + self.model + index + self.aux + body
        framing = sum(self.unit_framing) + len(self.aux)
        acct = Accounting(header=len(header), model=len(self.model), index=len(index), framing=framing,
                          payload=len(body) - sum(self.unit_framing))
        assert acct.total == len(archive), 'accounting does not sum to the archive length'
        return archive, acct

    def _pack_partitioned(self, index_width: int | None) -> tuple[bytes, Accounting]:
        assert self.parts is not None
        if not 0 < len(self.parts) < 256:
            raise ValueError('a partitioned archive needs 1..255 parts')
        subs = [p.pack(index_width) for p in self.parts]
        header = MAGIC + bytes([M_PARTITIONED, 0, MODEL_NONE, len(self.parts)]) + struct.pack('<II', self.n_records, 0)
        table = b''.join(struct.pack('<II', p.n_records, len(a)) for p, (a, _) in zip(self.parts, subs))
        archive = header + table + b''.join(a for a, _ in subs)
        acct = Accounting(header=len(header) + len(table))
        for _, sub_acct in subs:
            acct = acct + sub_acct
        assert acct.total == len(archive), 'accounting does not sum to the archive length'
        return archive, acct

    def lane_form_bytes(self) -> int:
        """Size this content would have in the lane's own container form: a 10-byte header, the model,
        4 index bytes per stored unit (and per record for the block method), then the stored units.
        A partitioned archive is charged one header, every part's model and index, and 4 bytes per
        extra part for the split point, which is what the lane's two-table BIT3 container carries."""
        if self.parts is not None:
            inner = sum(p.lane_form_bytes() - LANE_HEADER_BYTES for p in self.parts)
            return LANE_HEADER_BYTES + inner + 4 * (len(self.parts) - 1)
        idx = LANE_INDEX_WIDTH * len(self.units)
        if self.rec_raw_ends is not None:
            idx += LANE_INDEX_WIDTH * len(self.rec_raw_ends)
        return LANE_HEADER_BYTES + len(self.model) + idx + len(self.aux) + sum(len(u) for u in self.units)

    def stored_bytes(self) -> int:
        """Stored units plus aux: the part of the archive that grows with the number of records,
        index excluded."""
        if self.parts is not None:
            return sum(p.stored_bytes() for p in self.parts)
        return len(self.aux) + sum(len(u) for u in self.units)

    def model_bytes(self) -> int:
        if self.parts is not None:
            return sum(p.model_bytes() for p in self.parts)
        return len(self.model)
