#!/usr/bin/env python3
"""Bounded FX2 integer range coding and an exact donor/parent mixture.

The range-coder semantics follow the pinned external FX2/CMIX sources below.
Inputs are already quantized probabilities of bit 1; no float discretization
is performed. ``low`` and ``high`` are the native inclusive x1/x2 interval.

Native decoding reads zero beyond EOF. A raw payload therefore cannot establish
its own length, decoded bit count, integrity, or canonical termination. Pass a
trusted declared length/hash to Decoder and verify the complete decoded data
and canonical re-encoding in the enclosing format. Hashes detect corruption;
they do not authenticate an untrusted framing declaration.

Default work bounds cover synthetic fixtures. Explicitly larger limits require
their own experiment authority; these classes confer no launch or score credit.
ParentMixture exports state for synchronization, not a restore/checkpoint API.
"""

from __future__ import annotations

import hashlib
import json
import math
import re

NATIVE_REFERENCE_SOURCES = {
    "results/fx2_weight_native_transfer250k_q0_v1/work/native/src/coder/encoder.cpp":
        "e1586dca62d959dff81f156512d37a22a5e2abbb332c77962e0e8a0a0c646d29",
    "results/fx2_weight_native_transfer250k_q0_v1/work/native/src/coder/decoder.cpp":
        "cfed5d718bc6d1e797bb7c22be769040a7407086baf7918fcb522fd558c25258",
}
Q16 = 65536
MASK32 = 0xFFFFFFFF
DEFAULT_MAX_BITS = 8192 * 8
MAX_BITS = 1000000 * 8
MAX_PAYLOAD_BYTES = MAX_BITS * 2 + 1
MAX_DONOR_BYTES = 256


def _integer(value: int, minimum: int, maximum: int, name: str) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an integer in {minimum}..{maximum}")
    return value


def _limits(max_bits: int, max_payload_bytes: int | None) -> tuple[int, int]:
    max_bits = _integer(max_bits, 0, MAX_BITS, "max_bits")
    if max_payload_bytes is None:
        max_payload_bytes = 2 * max_bits + 1
    return max_bits, _integer(max_payload_bytes, 1, MAX_PAYLOAD_BYTES, "max_payload_bytes")


class Encoder:
    """encode(bit, q), then finish(); finish is idempotent and closes encoding."""

    def __init__(self, *, max_bits: int = DEFAULT_MAX_BITS,
                 max_payload_bytes: int | None = None):
        self.max_bits, self.max_payload_bytes = _limits(max_bits, max_payload_bytes)
        self.low, self.high, self.bit_count = 0, MASK32, 0
        self._output = bytearray()
        self._finished: bytes | None = None

    def encode(self, bit: int, q: int) -> None:
        _integer(bit, 0, 1, "bit")
        _integer(q, 1, Q16 - 1, "q")
        if self._finished is not None:
            raise ValueError("encoder is finished")
        if self.bit_count >= self.max_bits:
            raise ValueError("encoder bit budget exhausted")
        low, high = self.low, self.high
        mid = low + ((high - low) * q // Q16)
        if bit:
            high = mid
        else:
            low = mid + 1
        emitted = bytearray()
        while (low ^ high) & 0xFF000000 == 0:
            emitted.append(high >> 24)
            low = (low << 8) & MASK32
            high = ((high << 8) | 255) & MASK32
        # Reserve the required final byte before mutating state.
        if len(self._output) + len(emitted) + 1 > self.max_payload_bytes:
            raise ValueError("encoder payload budget exhausted")
        self.low, self.high = low, high
        self._output.extend(emitted)
        self.bit_count += 1

    def finish(self) -> bytes:
        if self._finished is None:
            # encode already performs native normalization after every bit.
            self._output.append(self.high >> 24)
            self._finished = bytes(self._output)
        return self._finished


class Decoder:
    """Native zero-fill decoder; enclosing framing must establish completeness."""

    def __init__(self, payload: bytes, *, max_bits: int = DEFAULT_MAX_BITS,
                 max_payload_bytes: int | None = None,
                 expected_payload_bytes: int | None = None,
                 payload_sha256: str | None = None):
        self.max_bits, self.max_payload_bytes = _limits(max_bits, max_payload_bytes)
        if not isinstance(payload, bytes) or not 1 <= len(payload) <= self.max_payload_bytes:
            raise ValueError("payload must be nonempty bytes within the payload budget")
        if expected_payload_bytes is not None:
            _integer(expected_payload_bytes, 1, self.max_payload_bytes, "expected_payload_bytes")
            if len(payload) != expected_payload_bytes:
                raise ValueError("declared payload length differs")
        if payload_sha256 is not None:
            if not isinstance(payload_sha256, str) or re.fullmatch(r"[0-9a-f]{64}", payload_sha256) is None:
                raise ValueError("payload_sha256 must be a lowercase SHA-256 hex digest")
            if hashlib.sha256(payload).hexdigest() != payload_sha256:
                raise ValueError("declared payload digest differs")
        self.payload = payload
        self.low, self.high, self.bit_count = 0, MASK32, 0
        self.read_position = 0
        self.code = 0
        for _ in range(4):
            self.code = ((self.code << 8) | self._read_byte()) & MASK32

    def _read_byte(self) -> int:
        value = self.payload[self.read_position] if self.read_position < len(self.payload) else 0
        self.read_position += 1
        return value

    def decode(self, q: int) -> int:
        _integer(q, 1, Q16 - 1, "q")
        if self.bit_count >= self.max_bits:
            raise ValueError("decoder bit budget exhausted")
        mid = self.low + ((self.high - self.low) * q // Q16)
        bit = int(self.code <= mid)
        if bit:
            self.high = mid
        else:
            self.low = mid + 1
        while (self.low ^ self.high) & 0xFF000000 == 0:
            self.low = (self.low << 8) & MASK32
            self.high = ((self.high << 8) | 255) & MASK32
            self.code = ((self.code << 8) | self._read_byte()) & MASK32
        self.bit_count += 1
        return bit


class ParentMixture:
    """Equal-prior deterministic donor versus the supplied parent sequence.

    Masses share an implicit denominator and are reduced by their GCD. A donor
    match multiplies its mass by 65536 and the parent mass by the parent's Q16
    truth numerator. A mismatch sets donor mass to zero. After mismatch or
    exhaustion, predictions equal the supplied parent and masses stop growing.
    Bits within each donor byte are most significant first.
    """

    def __init__(self, *, max_bits: int = DEFAULT_MAX_BITS):
        self.max_bits = _integer(max_bits, 0, MAX_BITS, "max_bits")
        self.bit_count = 0
        self.reset_count = 0
        self._pending: tuple[int, int, int | None] | None = None
        self._donor: bytes | None = None
        self._position = 0
        self._donor_mass, self._parent_mass = 0, 1

    def reset(self, donor: bytes | None) -> None:
        if self._pending is not None:
            raise ValueError("cannot reset with an unobserved prediction")
        if donor is not None and (not isinstance(donor, bytes) or len(donor) > MAX_DONOR_BYTES):
            raise ValueError("donor must be None or at most 256 bytes")
        if self.reset_count >= self.max_bits + 1:
            raise ValueError("mixture reset budget exhausted")
        self._donor, self._position = donor, 0
        self._donor_mass, self._parent_mass = int(bool(donor)), 1
        self.reset_count += 1

    def predict(self, parent_q: int) -> int:
        _integer(parent_q, 1, Q16 - 1, "parent_q")
        if self._pending is not None:
            raise ValueError("previous parent probability is pending observation")
        if self.bit_count >= self.max_bits:
            raise ValueError("mixture bit budget exhausted")
        donor_bit = None
        mixed = parent_q
        if self._donor_mass and self._donor is not None and self._position < 8 * len(self._donor):
            donor_bit = (self._donor[self._position // 8] >> (7 - self._position % 8)) & 1
            mixed = (self._parent_mass * parent_q + self._donor_mass * Q16 * donor_bit) // (
                self._parent_mass + self._donor_mass)
            mixed = max(1, min(Q16 - 1, mixed))
        self._pending = parent_q, mixed, donor_bit
        return mixed

    def observe(self, bit: int) -> None:
        _integer(bit, 0, 1, "bit")
        if self._pending is None:
            raise ValueError("predict must precede observe")
        if self.bit_count >= self.max_bits:
            raise ValueError("mixture bit budget exhausted")
        parent_q, _, donor_bit = self._pending
        if donor_bit is not None:
            if bit != donor_bit:
                self._donor_mass, self._parent_mass = 0, 1
            else:
                donor_mass = self._donor_mass * Q16
                parent_mass = self._parent_mass * (parent_q if bit else Q16 - parent_q)
                divisor = math.gcd(donor_mass, parent_mass)
                self._donor_mass, self._parent_mass = donor_mass // divisor, parent_mass // divisor
        if self._donor is not None and self._position < 8 * len(self._donor):
            self._position += 1
        self.bit_count += 1
        self._pending = None

    def export(self) -> dict:
        """Bounded JSON-safe state; hexadecimal avoids decimal integer limits."""
        return {
            "schema": "gamma.enwiki9.causal-field-parent-mixture-state.v1",
            "max_bits": self.max_bits, "bit_count": self.bit_count,
            "reset_count": self.reset_count,
            "donor_hex": None if self._donor is None else self._donor.hex(),
            "donor_bit_position": self._position,
            "donor_mass_hex": format(self._donor_mass, "x"),
            "parent_mass_hex": format(self._parent_mass, "x"),
            "pending": None if self._pending is None else {
                "parent_q": self._pending[0], "mixed_q": self._pending[1],
                "donor_bit": self._pending[2],
            },
        }

    def state_digest(self) -> str:
        data = json.dumps(self.export(), sort_keys=True, separators=(",", ":")).encode("ascii")
        return hashlib.sha256(data).hexdigest()
