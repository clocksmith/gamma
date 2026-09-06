"""Causal binary predictor boundary; probabilities describe the next bit.

Frontends must adapt their own coordinates explicitly. Raw-byte, WRT-byte and
coder-event traces are different inputs even when their bit counts coincide.
This module's integer coder is a fixture codec, not a prize-qualified package.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
import hashlib
import json


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


@dataclass(frozen=True)
class Frontend:
    name: str
    version: int
    coordinates: str
    symbol_order: str

    def require(self, other: "Frontend") -> None:
        if self != other:
            raise ValueError("frontend mismatch: an explicit adapter is required")


RAW_MSB = Frontend("raw-bytes", 1, "zero-based-byte-and-bit", "msb-first")


@dataclass(frozen=True)
class TraceIdentity:
    frontend: Frontend
    source_sha256: str
    initial_state_sha256: str
    population_sha256: str
    coordinate_start: int

    def require(self, other: "TraceIdentity") -> None:
        if self != other:
            raise ValueError("trace reuse requires identical frontend, source, state and population coordinates")


class Predictor(ABC):
    """One predict() then one update(decoded_bit), with no truth argument to predict.

    Concrete initialization and serialized model state must be deterministic.
    A pending prediction is serialized too, so resumption cannot skip an update.
    """
    def __init__(self, frontend: Frontend):
        self.frontend = frontend
        self.position = 0
        self._pending = None

    def predict(self) -> int:
        if self._pending is not None:
            raise ValueError("update the decoded bit before predicting again")
        probability = self._predict()
        if type(probability) is not int or not 1 <= probability <= 65535:
            raise ValueError("probability must be an integer Q16 P(bit=1), strictly between zero and one")
        self._pending = probability
        return probability

    def update(self, decoded_bit: int) -> None:
        if self._pending is None:
            raise ValueError("predict must precede the decoded-symbol update")
        if type(decoded_bit) is not int or decoded_bit not in (0, 1):
            raise ValueError("decoded symbol must be a bit")
        self._update(decoded_bit)
        self.position += 1
        self._pending = None

    def serialize(self) -> bytes:
        return canonical({"frontend": asdict(self.frontend), "position": self.position,
                          "pending": self._pending, "model": self._export_state()})

    def state_digest(self) -> str:
        return hashlib.sha256(self.serialize()).hexdigest()

    @abstractmethod
    def _predict(self) -> int: ...

    @abstractmethod
    def _update(self, decoded_bit: int) -> None: ...

    @abstractmethod
    def _export_state(self) -> dict: ...

    @classmethod
    @abstractmethod
    def restore(cls, payload: bytes, frontend: Frontend) -> "Predictor": ...


class CountingPredictor(Predictor):
    """Deterministic context-count fixture, useful for adapters and codec tests."""
    def __init__(self, order: int = 0, frontend: Frontend = RAW_MSB):
        super().__init__(frontend)
        if type(order) is not int or not 0 <= order <= 12:
            raise ValueError("fixture order must be 0..12")
        self.order = order
        self.context = 0
        self.counts = [[1, 1] for _ in range(1 << order)]

    def _predict(self):
        zero, one = self.counts[self.context]
        return max(1, min(65535, one * 65536 // (zero + one)))

    def _update(self, decoded_bit):
        row = self.counts[self.context]
        row[decoded_bit] += 1
        if sum(row) >= 32768:
            row[:] = [max(1, (value + 1) // 2) for value in row]
        self.context = ((self.context << 1) | decoded_bit) & ((1 << self.order) - 1)

    def _export_state(self):
        return {"kind": "context-count-fixture-v1", "order": self.order,
                "context": self.context, "counts": self.counts}

    @classmethod
    def restore(cls, payload, frontend=RAW_MSB):
        value = json.loads(payload)
        frontend.require(Frontend(**value["frontend"]))
        model = value["model"]
        if model["kind"] != "context-count-fixture-v1":
            raise ValueError("unknown predictor state")
        result = cls(model["order"], frontend)
        counts = model["counts"]
        if len(counts) != 1 << result.order or any(
            len(row) != 2 or any(type(n) is not int or not 1 <= n < 32768 for n in row)
            for row in counts
        ):
            raise ValueError("invalid count state")
        if type(model["context"]) is not int or not 0 <= model["context"] < len(counts):
            raise ValueError("invalid context")
        if type(value["position"]) is not int or value["position"] < 0:
            raise ValueError("invalid position")
        if value["pending"] is not None and (type(value["pending"]) is not int or not 1 <= value["pending"] <= 65535):
            raise ValueError("invalid pending probability")
        result.counts, result.context = counts, model["context"]
        result.position, result._pending = value["position"], value["pending"]
        return result


def _split(low, high, probability_one):
    return low + ((high - low + 1) * (65536 - probability_one) // 65536) - 1


def encode(raw: bytes, predictor: Predictor) -> bytes:
    """32-bit binary arithmetic fixture; decoder length is explicitly framed."""
    predictor.frontend.require(RAW_MSB)
    low, high, pending = 0, 0xffffffff, 0
    output = bytearray()
    accumulator = used = 0

    def emit(bit):
        nonlocal accumulator, used
        accumulator = (accumulator << 1) | bit
        used += 1
        if used == 8:
            output.append(accumulator)
            accumulator = used = 0

    def resolve(bit):
        nonlocal pending
        emit(bit)
        for _ in range(pending):
            emit(1 - bit)
        pending = 0

    for symbol in raw:
        for shift in range(7, -1, -1):
            probability = predictor.predict()
            bit = (symbol >> shift) & 1
            split = _split(low, high, probability)
            if bit:
                low = split + 1
            else:
                high = split
            predictor.update(bit)
            while True:
                if high < 0x80000000:
                    resolve(0)
                elif low >= 0x80000000:
                    resolve(1)
                    low -= 0x80000000; high -= 0x80000000
                elif low >= 0x40000000 and high < 0xc0000000:
                    pending += 1
                    low -= 0x40000000; high -= 0x40000000
                else:
                    break
                low *= 2; high = high * 2 + 1
    pending += 1
    resolve(0 if low < 0x40000000 else 1)
    if used:
        output.append(accumulator << (8 - used))
    return b"GPI1" + len(raw).to_bytes(8, "big") + bytes(output) + b"\0\0\0\0"


def decode(archive: bytes, predictor: Predictor, *, maximum_bytes: int = 1_000_000) -> bytes:
    predictor.frontend.require(RAW_MSB)
    if len(archive) < 17 or archive[:4] != b"GPI1":
        raise ValueError("invalid fixture archive")
    length = int.from_bytes(archive[4:12], "big")
    if length > maximum_bytes:
        raise ValueError("fixture decode exceeds output budget")
    payload, cursor = archive[12:], 0

    def take():
        nonlocal cursor
        if cursor >= len(payload) * 8:
            raise ValueError("truncated fixture archive")
        bit = (payload[cursor // 8] >> (7 - cursor % 8)) & 1
        cursor += 1
        return bit

    low, high, code = 0, 0xffffffff, 0
    for _ in range(32):
        code = code * 2 + take()
    output = bytearray()
    for _ in range(length):
        symbol = 0
        for _ in range(8):
            split = _split(low, high, predictor.predict())
            bit = int(code > split)
            if bit:
                low = split + 1
            else:
                high = split
            predictor.update(bit)
            symbol = symbol * 2 + bit
            while True:
                if high < 0x80000000:
                    pass
                elif low >= 0x80000000:
                    low -= 0x80000000; high -= 0x80000000; code -= 0x80000000
                elif low >= 0x40000000 and high < 0xc0000000:
                    low -= 0x40000000; high -= 0x40000000; code -= 0x40000000
                else:
                    break
                low *= 2; high = high * 2 + 1; code = code * 2 + take()
        output.append(symbol)
    return bytes(output)
