#!/usr/bin/env python3
"""Preserve canonical audit bytes while bounding temporary sorting memory."""
import heapq
import marshal
from pathlib import Path
import struct
import tempfile
import types

from opcode_field_repair_cli_v1 import Audit as OriginalAudit, packed, feed

CHUNK_RECORDS = 4096
CHUNK_BYTES = 1048576
FAN_IN = 16
SEGMENT_BYTES = 8388608
SCRATCH_ROOT = None
HEADER = struct.Struct('>IQ')


def records(paths):
    for path in paths:
        with path.open('rb') as stream:
            while header := stream.read(HEADER.size):
                if len(header) != HEADER.size:
                    raise ValueError('truncated audit sort header')
                length, ordinal = HEADER.unpack(header)
                data = stream.read(length)
                if len(data) != length:
                    raise ValueError('truncated audit sort key')
                yield data, ordinal


def write_run(directory, number, rows):
    paths = []
    stream = None
    size = 0
    try:
        for data, ordinal in rows:
            if stream is None or size + HEADER.size + len(data) > SEGMENT_BYTES:
                if stream is not None:
                    stream.close()
                path = directory / f'run-{number}-{len(paths)}'
                paths.append(path)
                stream = path.open('xb')
                size = 0
            stream.write(HEADER.pack(len(data), ordinal))
            stream.write(data)
            size += HEADER.size + len(data)
    finally:
        if stream is not None:
            stream.close()
    return paths


def ordered_keys(table):
    """Stable order of marshal-v2 keys, identical to sorted(table, key=packed)."""
    if SCRATCH_ROOT is None:
        raise ValueError('audit sort requires an explicitly owned scratch directory')
    with tempfile.TemporaryDirectory(prefix='audit-sort-', dir=SCRATCH_ROOT) as temporary:
        directory = Path(temporary)
        runs, chunk = [], []
        size = number = 0
        for ordinal, key in enumerate(table):
            data = packed(key)
            chunk.append((data, ordinal))
            size += len(data) + HEADER.size
            if len(chunk) >= CHUNK_RECORDS or size >= CHUNK_BYTES:
                chunk.sort()
                runs.append(write_run(directory, number, chunk))
                number += 1
                chunk.clear(); size = 0
        if chunk:
            chunk.sort()
            runs.append(write_run(directory, number, chunk))
            number += 1
            chunk.clear()
        while len(runs) > FAN_IN:
            next_runs = []
            for start in range(0, len(runs), FAN_IN):
                group = runs[start:start + FAN_IN]
                merged = heapq.merge(*(records(paths) for paths in group))
                next_runs.append(write_run(directory, number, merged))
                number += 1
                for paths in group:
                    for path in paths:
                        path.unlink()
            runs = next_runs
        for data, ordinal in heapq.merge(*(records(paths) for paths in runs)):
            yield marshal.loads(data)


def table_hash(hasher, name, table, value=lambda x: x, include=lambda x: True):
    feed(hasher, name)
    keys = ordered_keys(table)
    try:
        for key in keys:
            row = table[key]
            if include(row):
                feed(hasher, (key, value(row)))
    finally:
        keys.close()


class Audit(OriginalAudit):
    finish = types.FunctionType(OriginalAudit.finish.__code__,
        dict(OriginalAudit.finish.__globals__, table_hash=table_hash), 'finish')
