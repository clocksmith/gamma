#!/usr/bin/env python3
"""Zero-table online macro tokenizer for enwik probes.

The encoder and decoder both start with the 256 byte literals.  As emitted
symbols repeat, the next unused high-byte slot is bound to the repeated symbol
pair.  Token definitions store their expanded bytes, so later token creation is
independent of recursive table mutation.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path


ESC = 128
TOKEN_BASE = 129
TOKEN_SLOTS = 127
FIRST_TOKEN = 256


class OnlineBpe:
    def __init__(self, threshold: int) -> None:
        self.threshold = threshold
        self.next_token = FIRST_TOKEN
        self.expansions: dict[int, bytes] = {i: bytes([i]) for i in range(256)}
        self.pair_to_token: dict[tuple[int, int], int] = {}
        self.pair_counts: defaultdict[tuple[int, int], int] = defaultdict(int)
        self.prev_symbol: int | None = None
        self.tokens_created = 0
        self.tokens_emitted = 0
        self.raw_emitted = 0
        self.escaped_raw = 0
        self.input_pos = 0

    def _observe_symbol(self, sym: int) -> None:
        if self.prev_symbol is not None:
            pair = (self.prev_symbol, sym)
            if pair not in self.pair_to_token and self.next_token < FIRST_TOKEN + TOKEN_SLOTS:
                self.pair_counts[pair] += 1
                if self.pair_counts[pair] >= self.threshold:
                    token = self.next_token
                    self.next_token += 1
                    self.pair_to_token[pair] = token
                    self.expansions[token] = self.expansions[pair[0]] + self.expansions[pair[1]]
                    self.tokens_created += 1
        self.prev_symbol = sym

    def _emit_symbol(self, out: bytearray, sym: int) -> None:
        if sym < 128:
            out.append(sym)
            self.raw_emitted += 1
        elif sym < 256:
            out.extend((ESC, sym))
            self.raw_emitted += 1
            self.escaped_raw += 1
        else:
            out.append(TOKEN_BASE + (sym - FIRST_TOKEN))
            self.tokens_emitted += 1
        self._observe_symbol(sym)

    def _decode_symbol(self, data: bytes, pos: int) -> tuple[int, int]:
        b = data[pos]
        if b < ESC:
            return b, pos + 1
        if b == ESC:
            if pos + 1 >= len(data):
                raise ValueError("truncated escape")
            raw = data[pos + 1]
            if raw < 128:
                raise ValueError("noncanonical escaped low byte")
            return raw, pos + 2
        token = FIRST_TOKEN + (b - TOKEN_BASE)
        if token not in self.expansions:
            raise ValueError(f"unknown token byte {b} at encoded offset {pos}")
        return token, pos + 1

    def _candidate_tokens(self, data: bytes, pos: int) -> list[int]:
        first = data[pos]
        matches = []
        for token in range(FIRST_TOKEN, self.next_token):
            expansion = self.expansions[token]
            if expansion and expansion[0] == first and data.startswith(expansion, pos):
                matches.append(token)
        matches.sort(key=lambda t: len(self.expansions[t]), reverse=True)
        return matches

    def encode(self, data: bytes) -> bytes:
        out = bytearray()
        pos = 0
        n = len(data)
        while pos < n:
            chosen = None
            for token in self._candidate_tokens(data, pos):
                if len(self.expansions[token]) > 1:
                    chosen = token
                    break
            if chosen is None:
                sym = data[pos]
                pos += 1
            else:
                sym = chosen
                pos += len(self.expansions[chosen])
            self._emit_symbol(out, sym)
            self.input_pos = pos
        return bytes(out)

    def decode(self, data: bytes) -> bytes:
        out = bytearray()
        pos = 0
        while pos < len(data):
            sym, pos = self._decode_symbol(data, pos)
            out.extend(self.expansions[sym])
            self._observe_symbol(sym)
        return bytes(out)


def run_encode(args: argparse.Namespace) -> None:
    source = Path(args.input).read_bytes()
    coder = OnlineBpe(args.threshold)
    encoded = coder.encode(source)
    Path(args.output).write_bytes(encoded)
    if args.verify:
        decoded = OnlineBpe(args.threshold).decode(encoded)
        if decoded != source:
            raise SystemExit("roundtrip failed")
    print(f"input_bytes={len(source)}")
    print(f"encoded_bytes={len(encoded)}")
    print(f"delta_bytes={len(encoded) - len(source)}")
    print(f"tokens_created={coder.tokens_created}")
    print(f"tokens_emitted={coder.tokens_emitted}")
    print(f"raw_emitted={coder.raw_emitted}")
    print(f"escaped_raw={coder.escaped_raw}")


def run_decode(args: argparse.Namespace) -> None:
    encoded = Path(args.input).read_bytes()
    decoded = OnlineBpe(args.threshold).decode(encoded)
    Path(args.output).write_bytes(decoded)
    print(f"encoded_bytes={len(encoded)}")
    print(f"decoded_bytes={len(decoded)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("encode", "decode"))
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("--threshold", type=int, default=8)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.threshold < 2:
        raise SystemExit("--threshold must be at least 2")
    if args.mode == "encode":
        run_encode(args)
    else:
        run_decode(args)


if __name__ == "__main__":
    main()
