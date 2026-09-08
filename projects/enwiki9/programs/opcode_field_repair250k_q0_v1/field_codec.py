"""Authenticated private parent definitions with only the exposed f changed.

Optional audit callbacks are experiment machinery. Every operation constructs
fresh definitions. Encoder search tables never become decoder side inputs.
"""
from __future__ import annotations
import hashlib
import lzma
from pathlib import Path
import struct

PACKED_SHA256 = "3e9c9ed25997ad10bac94575fb3da5009530ba04fa961da14a016fe89eec9a15"
EXPANDED_SHA256 = "4f37b0da3fd7642533ca8d2ac865019c218c2508482aba85f9a2c1d35cde6cb4"
MAX_RAW = 1000000
MAX_ARCHIVE = 32 * 1024**2
OPEN = {15: 1, 17: 2, 9: 3, 11: 4, 13: 5, 1: 6}
CLOSE = frozenset((16, 18, 10, 12, 14, 2))
POLICY = "complete-opcode-field-only-v1"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def source(candidate_root):
    packed = (Path(candidate_root) / "p").read_bytes()
    require(len(packed) == 4767 and digest(packed) == PACKED_SHA256, "packed parent changed")
    decoder = lzma.LZMADecompressor(format=lzma.FORMAT_ALONE)
    expanded = decoder.decompress(packed, max_length=65536)
    require(decoder.eof and not decoder.unused_data and digest(expanded) == EXPANDED_SHA256, "expanded parent changed")
    return expanded.decode("ascii")


def untouched(candidate_root):
    namespace = {"__name__": "private_untouched_opcode_parent"}
    exec(compile(source(candidate_root), "<authenticated-opcode-parent>", "exec"), namespace)
    return namespace


class Field:
    """Only complete opcode pairs change f; escaped zero is one literal."""
    def __init__(self):
        self.f = 0
        self.pending = False

    def up(self, byte):
        if self.pending:
            require(byte == 255 or 1 <= byte <= 39, "unknown opcode")
            if byte in OPEN:
                self.f = OPEN[byte]
            elif byte in CLOSE:
                self.f = 0
            self.pending = False
        elif byte == 0:
            self.pending = True


def private(candidate_root, arm, modeled_limit, audit=None, estimator=False):
    require(arm in "PKD" and len(arm) == 1, "invalid arm")
    text = source(candidate_root)
    # Exact hooks expose live locals without rewriting the retained algorithms.
    for before, after in {
        ' out=a.fin();_S=': ' _capture(a,lit,st,tok,ch,d)\n out=a.fin();_S=',
        ' return bytes(o[:n])': ' _capture(a,lit,st,tok,ch,bytes(o))\n return bytes(o[:n])',
    }.items():
        require(text.count(before) == 1, "legacy capture site differs")
        text = text.replace(before, after)
    ns = {"__name__": "private_opcode_field_" + arm}
    exec(compile(text, "<authenticated-opcode-field-adapter>", "exec"), ns)
    BaseGST, BaseLIT, BaseCM, BaseTOK, BaseAC = [ns[k] for k in ("GST", "LIT", "CM", "TOK", "AC")]
    BaseAdd = ns["addc"]
    captured = {}

    class State(BaseGST):
        def __init__(self):
            super().__init__()
            self.modeled_f = self.f
            self.field = Field() if arm != "P" else None
            self.position = 0

        def up(self, byte):
            require(self.position < modeled_limit, "modeled output exceeds declared length")
            self.f = self.modeled_f
            super().up(byte)
            self.modeled_f = self.f
            if self.field is not None:
                self.field.up(byte)
                if arm == "D":
                    self.f = self.field.f
            self.position += 1
            if audit is not None:
                audit.byte(self, byte)

    class Literal(BaseLIT):
        def predict(self, state, prefix, bit_index):
            values = super().predict(state, prefix, bit_index)
            if audit is not None:
                pf, keys, bucket, mixed, stretches, weights = values
                audit.probability((0, state.position, prefix, bit_index, pf, tuple(keys), bucket,
                                   mixed, tuple(stretches), tuple(weights)))
            return values

        def update(self, keys, bucket, mixed, stretches, weights, bit):
            super().update(keys, bucket, mixed, stretches, weights, bit)
            if audit is not None:
                audit.transition((0, bit, tuple((i, key, tuple(self.tt[i][key])) for i, key in enumerate(keys)),
                                  bucket, tuple(self.sse[bucket]), tuple(weights)))

    class Count(BaseCM):
        def cf(self, value):
            if audit is not None:
                audit.probability((1, self.where, tuple(self.c), self.t))
            return super().cf(value)

        def find(self, target):
            if audit is not None:
                audit.probability((1, self.where, tuple(self.c), self.t))
            return super().find(target)

        def up(self, value):
            super().up(value)
            if audit is not None:
                audit.transition((1, self.where, value, tuple(self.c), self.t))

    class Tokens(BaseTOK):
        def m(self, table, key, size):
            model = super().m(table, key, size)
            if audit is not None:
                model.where = (next(i for i, name in enumerate(("e", "rl", "rd", "clv", "cix", "cln"))
                                    if getattr(self, name) is table), key)
            return model

        def __setattr__(self, name, value):
            super().__setattr__(name, value)
            if audit is not None and name == "last":
                audit.transition((2, value))

    class Coder(BaseAC):
        def __init__(self, data=None):
            super().__init__(data)
            self.payload = data
            self.shadow = BaseAC() if data is not None else None

        def enc(self, cumulative, frequency, total):
            before = (self.l, self.h)
            super().enc(cumulative, frequency, total)
            if audit is not None:
                audit.arithmetic((cumulative, frequency, total, before, (self.l, self.h, self.p)))

        def dec(self, cumulative, frequency, total):
            before = (self.l, self.h)
            self.shadow.enc(cumulative, frequency, total)
            super().dec(cumulative, frequency, total)
            require((self.l, self.h) == (self.shadow.l, self.shadow.h), "arithmetic inverse interval differs")
            if audit is not None:
                audit.arithmetic((cumulative, frequency, total, before, (self.l, self.h, self.shadow.p)))

    def add_chain(table, state, position):
        if audit is not None:
            update = tuple((key, tuple(table.get(key, ())[:-63])) for key in state.keys())
        BaseAdd(table, state, position)
        if audit is not None:
            audit.transition((3, position, update))

    def capture(coder, literal, state, tokens, chains, history):
        require(len(history) == state.position == modeled_limit, "modeled terminal length differs")
        require(state.field is None or not state.field.pending, "truncated opcode")
        if audit is not None:
            captured["audit"] = audit.finish(ns, coder if coder.shadow is None else coder.shadow,
                                               literal, state, tokens, chains, history)
        if coder.shadow is not None:
            require(coder.shadow.fin() == coder.payload, "noncanonical, truncated or trailing arithmetic payload")
        captured["state"] = state

    ns.update(GST=State, LIT=Literal, CM=Count, TOK=Tokens, AC=Coder, addc=add_chain, _capture=capture)
    if not estimator:
        def prefix(data):
            # Separate estimator models use the same field policy, but have no
            # observer and never enter decoder-common state or transition hashes.
            other, _ = private(candidate_root, arm, len(data), estimator=True)
            return other["lit_prefix"](data)
        ns["lit_prefix"] = prefix
    return ns, captured


def report(archive, raw, modeled, arm, captured):
    return {"schema": "gamma.enwiki9.opcode-field-codec-result.v1", "arm": arm, "policy": POLICY,
            "archive_bytes": len(archive), "raw_bytes": len(raw), "modeled_bytes": len(modeled),
            "raw_sha256": digest(raw), "modeled_sha256": digest(modeled), "archive_sha256": digest(archive),
            "packed_parent_sha256": PACKED_SHA256, "expanded_parent_sha256": EXPANDED_SHA256,
            "arm_value_bytes": 1, "archive_plus_arm_value_bytes": len(archive) + 1,
            "invocation_options": ["--arm", arm], "complete_options_bytes": None,
            "canonical_payload_reencode_pass": True, "complete_package_bytes": None,
            "full_corpus_score_bytes": None, "audit": captured.get("audit")}


def encode(raw, arm="D", *, candidate_root=None, audit=None):
    require(type(raw) is bytes and len(raw) <= MAX_RAW, "raw input bound differs")
    root = Path(candidate_root) if candidate_root is not None else Path(__file__).resolve().parent
    modeled = untouched(root)["oe"](raw)
    require(len(modeled) <= 2 * len(raw), "opcode expansion exceeds bound")
    ns, captured = private(root, arm, len(modeled), audit)
    inner = ns["compress_inner"](modeled)
    archive = struct.pack(">II", len(raw), len(modeled)) + inner
    require(len(archive) <= MAX_ARCHIVE, "archive byte limit exceeded")
    return archive, report(archive, raw, modeled, arm, captured)


def decode(archive, arm="D", *, candidate_root=None, audit=None):
    require(type(archive) is bytes and 9 <= len(archive) <= MAX_ARCHIVE, "archive byte limit differs")
    raw_length, modeled_length = struct.unpack(">II", archive[:8])
    require(raw_length <= MAX_RAW and modeled_length <= 2 * raw_length, "declared output bounds differ")
    root = Path(candidate_root) if candidate_root is not None else Path(__file__).resolve().parent
    ns, captured = private(root, arm, modeled_length, audit)
    try:
        modeled = ns["decompress_inner"](archive[8:], modeled_length)
        raw = ns["od"](modeled)
    except (IndexError, KeyError, ZeroDivisionError) as error:
        raise ValueError("malformed native archive") from error
    require(len(raw) == raw_length, "raw output length differs")
    return raw, report(archive, raw, modeled, arm, captured)
