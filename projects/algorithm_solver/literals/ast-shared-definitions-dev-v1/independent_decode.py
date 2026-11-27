"""Standalone SDA1 archive reader. Only AC32 and the grammar names come from A2's reader."""
from __future__ import annotations

from functools import lru_cache
import importlib.util
import json
from pathlib import Path
import struct
import zlib

path = Path(__file__).resolve().parent.parent / "a2-recursive-frames-v1" / "independent_decode.py"
spec = importlib.util.spec_from_file_location("frozen_a2_reader", path)
a2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a2)
NAMES = list(dict.fromkeys(["EXPR", "STMT", "PAT", "AUX", *a2.EXPR_TAGS, *a2.STMT_TAGS,
                           *a2.PAT_TAGS, *a2.EXPR_CONTEXTS, *a2.STMT_CONTEXTS, "PAT_DECL", "PAT_PARAM"]))


class Reader:
    def __init__(self, data):
        self.data, self.pos = data, 0

    def take(self, n):
        end = self.pos + n
        if end > len(self.data):
            raise ValueError("truncated section")
        result = self.data[self.pos:end]
        self.pos = end
        return result

    def byte(self):
        return self.take(1)[0]

    def uint(self):
        value, self.pos = a2.read_varint(self.data, self.pos)
        return value

    def block(self):
        return self.take(self.uint())

    def name(self):
        n = self.uint()
        if n > len(NAMES):
            raise ValueError("unknown grammar name id")
        return NAMES[n-1] if n else self.block().decode("utf-8")

    def atom(self):
        tag = self.byte()
        if tag == 0:
            return None
        if tag in (1, 2):
            return tag == 2
        if tag == 3:
            return self.uint()
        if tag == 4:
            return -1-self.uint()
        if tag == 5:
            return self.name()
        if tag == 6:
            return tuple(self.atom() for _ in range(self.uint()))
        if tag == 7:
            return struct.unpack(">d", self.take(8))[0]
        raise ValueError("invalid AST atom")

    def finish(self):
        if self.pos != len(self.data):
            raise ValueError("trailing bytes in section")


@lru_cache(maxsize=8192)
def signature(t):
    if t[0] == "HOLE":
        return (t[1:],)
    return tuple(h for c in t[4] for h in signature(c))


def substitute(t, args, shift=0):
    iterator = iter(args)
    def visit(node):
        if node[0] == "HOLE":
            arg = next(iterator)
            if arg[1] != node[1] or (arg[0] == "HOLE" and arg[2] != node[2]):
                raise ValueError("typed argument disagrees with definition")
            return arg
        _, group, tag, atoms, children = node
        if shift and tag == "Reg8":
            atoms = ((atoms[0]+shift) % 8,)
        return ("NODE", group, tag, atoms, tuple(visit(c) for c in children))
    return visit(t)


def decode_library(data):
    stream = Reader(data)
    if stream.take(3) != b"SL1":
        raise ValueError("invalid library magic")
    shared = stream.byte()
    if shared not in (0,1):
        raise ValueError("unknown library format")
    count, nshared = stream.uint(), stream.uint()
    if not shared and nshared:
        raise ValueError("scaffolds in a flat library")
    scaffolds, defs = [], []

    def term():
        opcode = stream.byte()
        if opcode == 0:
            group, tag, atoms = stream.name(), stream.name(), stream.atom()
            if not isinstance(atoms, tuple):
                raise ValueError("node atoms must be a tuple")
            return ("NODE", group, tag, atoms, tuple(term() for _ in range(stream.uint())))
        if opcode == 1:
            return ("HOLE", stream.name(), stream.name())
        if shared and opcode in (2, 3):
            table = scaffolds if opcode == 2 else defs
            index = stream.uint()
            if index >= len(table):
                raise ValueError("forward or out-of-bounds definition reference")
            pat = table[index]
            if opcode == 2:
                return pat
            return substitute(pat, tuple(term() for _ in signature(pat)))
        raise ValueError("illegal definition opcode")

    for table, n in ((scaffolds, nshared), (defs, count)):
        for _ in range(n):
            tree = term()
            if tree[0] != "NODE":
                raise ValueError("definition must have a concrete root")
            table.append(tree)
    stream.finish()
    return tuple(defs)


def inflate(block):
    decoder = zlib.decompressobj()
    data = decoder.decompress(block)
    if not decoder.eof or decoder.unused_data:
        raise ValueError("invalid compressed section framing")
    return data


def cumulative(weights, size):
    if len(weights) != size or any(type(w) is not int or w <= 0 for w in weights):
        raise ValueError("invalid probability table")
    out = [0]
    for weight in weights:
        out.append(out[-1] + weight)
    if out[-1] > 16384:
        raise ValueError("probability table exceeds AC32 limit")
    return out


def decode_archive(data):
    if len(data) < 8 or data[:4] != b"SDA1":
        raise ValueError("invalid archive magic")
    if data[-4:] != struct.pack(">I", zlib.crc32(data[:-4])):
        raise ValueError("archive checksum mismatch")
    stream = Reader(data[4:-4])
    library = stream.block()
    defs = decode_library(library)
    model_bytes = stream.block()
    if not model_bytes or model_bytes[0] not in (0, 1):
        raise ValueError("unknown probability model")
    rows, specialized = json.loads(inflate(model_bytes[1:]))
    if model_bytes[0] == 0 and specialized:
        raise ValueError("invalid dispatch prior")
    labels, tables = {}, {}
    for group, alphabet, weights in rows:
        if group in labels:
            raise ValueError("duplicate group")
        labels[group] = alphabet
        tables[(group,)] = cumulative(weights,len(alphabet)+1)
    for group, fid, ordinal, weights in specialized:
        key = group, fid, ordinal
        if (key in tables or fid not in range(len(defs)) or ordinal not in range(len(signature(defs[fid])))
                or signature(defs[fid])[ordinal][0] != group):
            raise ValueError("invalid conditional context")
        tables[key] = cumulative(weights, len(labels[group])+1)
    payload = Reader(stream.block())
    stream.finish()
    side = Reader(inflate(payload.block()))
    coded = payload.take(len(payload.data)-payload.pos)
    if not coded:
        raise ValueError("empty arithmetic stream")
    ac = a2.ArithmeticDecoder(coded)
    descriptions = []
    for _ in range(side.uint()):
        mode = side.byte()
        if mode not in (0,1):
            raise ValueError("invalid document mode")
        descriptions.append(side.block() if mode else side.uint())

    def read_tree(where):
        group = side.name()
        table = tables.get((group,*where), tables.get((group,))) if where else tables.get((group,))
        index = ac.decode(table) if table else 0
        if index:
            call, key = labels[group][index-1]
        else:
            call = side.byte()
            if call not in (0,1):
                raise ValueError("invalid escaped label")
            key = side.uint() if call else side.name()
        if not call:
            atoms = side.atom()
            if not isinstance(atoms,tuple):
                raise ValueError("node atoms must be a tuple")
            kids = [read_tree(None) for _ in range(side.uint())]
            return (("NODE",group,key,atoms,tuple(k[0] for k in kids)),
                    ("NODE",group,key,atoms,tuple(k[1] for k in kids)))
        if type(key) is not int or key not in range(len(defs)) or defs[key][1] != group:
            raise ValueError("invalid called definition")
        shift = side.byte()
        if shift >= 8:
            raise ValueError("register shift outside Z/8")
        args = [read_tree((key,i)) for i in range(len(signature(defs[key])))]
        call_tree = ("CALL",group,key,shift,tuple(a[0] for a in args))
        expanded = substitute(defs[key],tuple(a[1] for a in args),shift)
        return call_tree, expanded

    calls, docs = [], []
    for descr in descriptions:
        if isinstance(descr,bytes):
            calls.append(descr)
            docs.append(descr)
        else:
            trees = [read_tree(None) for _ in range(descr)]
            calls.append(tuple(t[0] for t in trees))
            docs.append(tuple(t[1] for t in trees))
    side.finish()
    return {"documents":docs,"calls":calls,"definitions":defs}
