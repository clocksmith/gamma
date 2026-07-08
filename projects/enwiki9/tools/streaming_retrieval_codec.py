#!/usr/bin/env python3
"""Bit-exact codec harness for the raw SRSTC lane.

This is an experimental proof harness, not an official Hutter package. It uses
the same causal raw-data model as streaming_retrieval_raw_shadow.py, writes an
actual arithmetic-coded payload, and decodes it by replaying the same model from
already reconstructed bytes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
from dataclasses import dataclass, field

from fx2_shadow_residual_coder import TOTAL, MAX_CODE, HALF, FIRST_QTR, THIRD_QTR, clamp_p1
from streaming_retrieval_raw_shadow import (
    BoundedByteTable,
    COPY_WEIGHT_SCALE,
    RawContextModel,
    TypedCopyChannel,
    byte_prior_p1,
    log_odds_mix_probability,
    make_byte_keys,
    parse_copy_offsets,
    selected_router_probability,
    selected_router_probability_by_band,
    update_router_losses,
)
from streaming_retrieval_shadow import (
    BandRouter,
    BoundedCounterTable,
    PartialByteState,
    RetrievalState,
    band_retrieval_p1,
    blend_probability,
    make_keys,
    retrieval_p1,
)


MAGIC = b"SRSTC1\x00"


@dataclass(frozen=True)
class SrstcConfig:
    suffix_len: int = 32
    sketch_len: int = 96
    base_order: int = 2
    p_buckets: int = 32
    min_support: int = 8
    blend_ppm: int = 640_000
    alpha2: int = 1
    base_table_cap_entries: int = 200_000
    retrieval_table_cap_entries: int = 200_000
    byte_table_cap_entries: int = 100_000
    partial_byte_family: str = "sketch"
    typed_key_profile: str = "base"
    expert_mode: str = "aggregate"
    router_decay_shift: int = 6
    router_abstain_margin_qbits: int = 128
    log_odds_mix: bool = False
    byte_prior_blend_ppm: int = 0
    byte_min_support: int = 8
    copy_channel_enabled: bool = False
    copy_channel_as_band: bool = False
    copy_channel_blend_ppm: int = 0
    copy_channel_cap_entries: int = 100_000
    copy_channel_top_k: int = 8
    copy_channel_max_key_scan: int = 32
    copy_channel_min_support: int = 4
    copy_channel_offsets: tuple[int, ...] = (0, -1, 1)
    copy_channel_age_shift: int = 14
    copy_channel_sketch_penalty: int = 1
    copy_channel_type_penalty: int = 2
    copy_channel_slot_penalty: int = 2
    copy_channel_word_penalty: int = 1
    copy_channel_column_penalty: int = 1
    copy_channel_offset_penalty: int = 2
    copy_channel_age_penalty: int = 1
    copy_channel_edit_penalty: int = 4
    copy_channel_edit_distance: int = 1
    copy_channel_escape_ppm: int = 512


class BitWriter:
    def __init__(self) -> None:
        self.buf = bytearray()
        self.current = 0
        self.nbits = 0
        self.total_bits = 0

    def write_bit(self, bit: int) -> None:
        self.current = ((self.current << 1) | (bit & 1)) & 0xFF
        self.nbits += 1
        self.total_bits += 1
        if self.nbits == 8:
            self.buf.append(self.current)
            self.current = 0
            self.nbits = 0

    def finish(self) -> bytes:
        if self.nbits:
            self.buf.append((self.current << (8 - self.nbits)) & 0xFF)
            self.current = 0
            self.nbits = 0
        return bytes(self.buf)


class BitReader:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload
        self.bit_pos = 0

    def read_bit(self) -> int:
        byte_index = self.bit_pos >> 3
        if byte_index >= len(self.payload):
            self.bit_pos += 1
            return 0
        bit = (self.payload[byte_index] >> (7 - (self.bit_pos & 7))) & 1
        self.bit_pos += 1
        return bit


class ArithmeticEncoder:
    def __init__(self) -> None:
        self.low = 0
        self.high = MAX_CODE
        self.pending = 0
        self.out = BitWriter()

    def _bit_plus_follow(self, bit: int) -> None:
        self.out.write_bit(bit)
        while self.pending:
            self.out.write_bit(1 - bit)
            self.pending -= 1

    def encode(self, bit: int, p1: int) -> None:
        p1 = clamp_p1(p1)
        zeros = TOTAL - p1
        span = self.high - self.low + 1
        split = self.low + (span * zeros) // TOTAL
        if bit:
            self.low = split
        else:
            self.high = split - 1

        while True:
            if self.high < HALF:
                self._bit_plus_follow(0)
            elif self.low >= HALF:
                self._bit_plus_follow(1)
                self.low -= HALF
                self.high -= HALF
            elif self.low >= FIRST_QTR and self.high < THIRD_QTR:
                self.pending += 1
                self.low -= FIRST_QTR
                self.high -= FIRST_QTR
            else:
                break
            self.low = (self.low << 1) & MAX_CODE
            self.high = ((self.high << 1) & MAX_CODE) | 1

    def finish(self) -> bytes:
        self.pending += 1
        if self.low < FIRST_QTR:
            self._bit_plus_follow(0)
        else:
            self._bit_plus_follow(1)
        return self.out.finish()


class ArithmeticDecoder:
    def __init__(self, payload: bytes) -> None:
        self.low = 0
        self.high = MAX_CODE
        self.reader = BitReader(payload)
        self.code = 0
        for _ in range(32):
            self.code = ((self.code << 1) | self.reader.read_bit()) & MAX_CODE

    def decode(self, p1: int) -> int:
        p1 = clamp_p1(p1)
        zeros = TOTAL - p1
        span = self.high - self.low + 1
        split = self.low + (span * zeros) // TOTAL
        if self.code < split:
            bit = 0
            self.high = split - 1
        else:
            bit = 1
            self.low = split

        while True:
            if self.high < HALF:
                pass
            elif self.low >= HALF:
                self.code -= HALF
                self.low -= HALF
                self.high -= HALF
            elif self.low >= FIRST_QTR and self.high < THIRD_QTR:
                self.code -= FIRST_QTR
                self.low -= FIRST_QTR
                self.high -= FIRST_QTR
            else:
                break
            self.low = (self.low << 1) & MAX_CODE
            self.high = ((self.high << 1) & MAX_CODE) | 1
            self.code = ((self.code << 1) & MAX_CODE) | self.reader.read_bit()
        return bit


@dataclass
class SrstcModel:
    config: SrstcConfig
    decoded: bytearray
    state: RetrievalState = field(init=False)
    partial_state: PartialByteState = field(default_factory=PartialByteState)
    base_model: RawContextModel = field(init=False)
    retrieval_table: BoundedCounterTable = field(init=False)
    byte_table: BoundedByteTable = field(init=False)
    router: BandRouter = field(init=False)
    copy_channel: TypedCopyChannel = field(init=False)

    def __post_init__(self) -> None:
        self.state = RetrievalState(
            data=self.decoded,
            suffix_len=self.config.suffix_len,
            sketch_len=self.config.sketch_len,
        )
        self.base_model = RawContextModel(
            cap_entries=self.config.base_table_cap_entries,
            p_buckets=self.config.p_buckets,
            order=self.config.base_order,
        )
        self.retrieval_table = BoundedCounterTable(
            cap_entries=self.config.retrieval_table_cap_entries
        )
        self.byte_table = BoundedByteTable(cap_entries=self.config.byte_table_cap_entries)
        self.router = BandRouter(decay_shift=self.config.router_decay_shift)
        self.copy_channel = TypedCopyChannel(
            cap_entries=(
                self.config.copy_channel_cap_entries
                if self.config.copy_channel_enabled
                else 0
            ),
            top_k=self.config.copy_channel_top_k,
            max_key_scan=self.config.copy_channel_max_key_scan,
            offsets=self.config.copy_channel_offsets,
            age_shift=self.config.copy_channel_age_shift,
            sketch_penalty=self.config.copy_channel_sketch_penalty,
            type_penalty=self.config.copy_channel_type_penalty,
            slot_penalty=self.config.copy_channel_slot_penalty,
            word_penalty=self.config.copy_channel_word_penalty,
            column_penalty=self.config.copy_channel_column_penalty,
            offset_penalty=self.config.copy_channel_offset_penalty,
            age_penalty=self.config.copy_channel_age_penalty,
            edit_penalty=self.config.copy_channel_edit_penalty,
            edit_distance=self.config.copy_channel_edit_distance,
            escape_ppm=self.config.copy_channel_escape_ppm,
        )

    def predict(self, pos: int, bit_pos: int) -> tuple[int, dict]:
        self.state.advance_to(pos)
        features = self.state.features()
        partial_len, partial_prefix = self.partial_state.advance_to(pos, bit_pos)
        history = bytes(self.state.tail)
        base_p1 = self.base_model.predict(
            history,
            bit_pos,
            partial_len,
            partial_prefix,
            self.config.alpha2,
        )
        keys = make_keys(
            features,
            bit_pos,
            base_p1,
            self.config.p_buckets,
            partial_len,
            partial_prefix,
            self.config.partial_byte_family,
            self.config.typed_key_profile,
        )
        byte_keys = make_byte_keys(features)
        copy_prior = self.copy_channel.prior_p1(
            self.decoded,
            pos,
            features,
            partial_len,
            partial_prefix,
            min_support=self.config.copy_channel_min_support,
            alpha_num=self.config.alpha2,
        )
        band_candidates = None
        selected_band = None
        if self.config.expert_mode in {"best_band", "best_band_abstain"}:
            band_candidates, _hits, _support = band_retrieval_p1(
                self.retrieval_table,
                keys,
                min_support=self.config.min_support,
                alpha_num=self.config.alpha2,
            )
            if self.config.copy_channel_as_band and copy_prior is not None:
                band_candidates[f"copy_{copy_prior.type_name}"] = (
                    copy_prior.p1,
                    max(1, copy_prior.support_weight // COPY_WEIGHT_SCALE),
                )
            corrected_p1, selected_band = self.router.choose(
                band_candidates,
                base_p1,
                self.config.blend_ppm,
                self.config.expert_mode == "best_band_abstain",
                self.config.router_abstain_margin_qbits,
            )
            corrected_p1 = selected_router_probability_by_band(
                base_p1,
                band_candidates,
                selected_band,
                self.config.blend_ppm,
                self.config.copy_channel_blend_ppm,
                {},
                self.config.log_odds_mix,
                corrected_p1,
            )
        else:
            prior_p1, _hits, _support = retrieval_p1(
                self.retrieval_table,
                keys,
                min_support=self.config.min_support,
                alpha_num=self.config.alpha2,
            )
            if self.config.expert_mode in {"no_regret", "no_regret_abstain"}:
                band_candidates = {}
                if prior_p1 is not None:
                    band_candidates["typed_retrieval"] = (prior_p1, max(1, _support))
                if copy_prior is not None:
                    band_candidates[f"copy_{copy_prior.type_name}"] = (
                        copy_prior.p1,
                        max(1, copy_prior.support_weight // COPY_WEIGHT_SCALE),
                    )
                corrected_p1, selected_band = self.router.choose(
                    band_candidates,
                    base_p1,
                    self.config.blend_ppm,
                    self.config.expert_mode == "no_regret_abstain",
                    self.config.router_abstain_margin_qbits,
                )
                corrected_p1 = selected_router_probability_by_band(
                    base_p1,
                    band_candidates,
                    selected_band,
                    self.config.blend_ppm,
                    self.config.copy_channel_blend_ppm,
                    {},
                    self.config.log_odds_mix,
                    corrected_p1,
                )
            elif self.config.log_odds_mix:
                corrected_p1 = log_odds_mix_probability(
                    base_p1,
                    [
                        (prior_p1, self.config.blend_ppm),
                        (
                            copy_prior.p1 if copy_prior is not None else None,
                            self.config.copy_channel_blend_ppm,
                        ),
                    ],
                )
            else:
                corrected_p1 = blend_probability(base_p1, prior_p1, self.config.blend_ppm)
                if copy_prior is not None and self.config.copy_channel_blend_ppm > 0:
                    corrected_p1 = blend_probability(
                        corrected_p1,
                        copy_prior.p1,
                        self.config.copy_channel_blend_ppm,
                    )
        byte_prior, _byte_hits, _byte_support = byte_prior_p1(
            self.byte_table,
            byte_keys,
            partial_len,
            partial_prefix,
            min_support=self.config.byte_min_support,
            alpha_num=self.config.alpha2,
        )
        if self.config.expert_mode in {"no_regret", "no_regret_abstain"} and byte_prior is not None:
            assert band_candidates is not None
            band_candidates["byte_prior"] = (byte_prior, max(1, _byte_support))
            corrected_p1, selected_band = self.router.choose(
                band_candidates,
                base_p1,
                self.config.blend_ppm,
                self.config.expert_mode == "no_regret_abstain",
                self.config.router_abstain_margin_qbits,
            )
            corrected_p1 = selected_router_probability_by_band(
                base_p1,
                band_candidates,
                selected_band,
                self.config.blend_ppm,
                self.config.copy_channel_blend_ppm,
                {},
                self.config.log_odds_mix,
                corrected_p1,
            )
        elif self.config.log_odds_mix:
            corrected_p1 = log_odds_mix_probability(
                corrected_p1,
                [(byte_prior, self.config.byte_prior_blend_ppm)],
            )
        elif self.config.byte_prior_blend_ppm > 0:
            corrected_p1 = blend_probability(
                corrected_p1, byte_prior, self.config.byte_prior_blend_ppm
            )
        return corrected_p1, {
            "base_p1": base_p1,
            "features": features,
            "keys": keys,
            "byte_keys": byte_keys,
            "band_candidates": band_candidates,
            "history": history,
            "partial_len": partial_len,
            "partial_prefix": partial_prefix,
        }

    def update(self, pos: int, bit_pos: int, bit: int, cached: dict) -> None:
        self.base_model.update(
            cached["history"],
            bit_pos,
            cached["partial_len"],
            cached["partial_prefix"],
            bit,
        )
        for key in cached["keys"]:
            self.retrieval_table.update(key, bit)
        if cached["band_candidates"] is not None:
            update_router_losses(
                self.router,
                bit,
                cached["band_candidates"],
                cached["base_p1"],
                self.config.blend_ppm,
                self.config.copy_channel_blend_ppm,
                {},
                self.config.log_odds_mix,
            )
        self.partial_state.observe(pos, bit)
        if self.partial_state.length == 8:
            byte_value = self.partial_state.prefix
            for key in cached["byte_keys"]:
                self.byte_table.update(key, byte_value)
            self.copy_channel.insert(pos, cached["features"])
            if len(self.decoded) == pos:
                self.decoded.append(byte_value)


def compress(data: bytes, config: SrstcConfig = SrstcConfig()) -> bytes:
    model = SrstcModel(config=config, decoded=bytearray(data))
    # The encoder state must see only completed previous bytes. Keep the full
    # data in a separate buffer and clear the decoded view used by the model.
    source = bytes(data)
    model.decoded.clear()
    encoder = ArithmeticEncoder()
    for pos, byte in enumerate(source):
        for bit_pos in range(8):
            p1, cached = model.predict(pos, bit_pos)
            bit = (byte >> (7 - bit_pos)) & 1
            encoder.encode(bit, p1)
            model.update(pos, bit_pos, bit, cached)
    payload = encoder.finish()
    return MAGIC + len(source).to_bytes(8, "big") + payload


def decompress(blob: bytes, config: SrstcConfig = SrstcConfig()) -> bytes:
    if len(blob) < len(MAGIC) + 8 or not blob.startswith(MAGIC):
        raise ValueError("invalid SRSTC codec payload")
    size = int.from_bytes(blob[len(MAGIC) : len(MAGIC) + 8], "big")
    payload = blob[len(MAGIC) + 8 :]
    model = SrstcModel(config=config, decoded=bytearray())
    decoder = ArithmeticDecoder(payload)
    for pos in range(size):
        for bit_pos in range(8):
            p1, cached = model.predict(pos, bit_pos)
            bit = decoder.decode(p1)
            model.update(pos, bit_pos, bit, cached)
    return bytes(model.decoded)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run an SRSTC codec roundtrip.")
    parser.add_argument("input", type=pathlib.Path)
    parser.add_argument("--limit-bytes", type=int, default=0)
    parser.add_argument("--archive-out", type=pathlib.Path)
    parser.add_argument("--receipt-out", type=pathlib.Path)
    parser.add_argument(
        "--expert-mode",
        choices=("aggregate", "best_band", "best_band_abstain", "no_regret", "no_regret_abstain"),
        default="aggregate",
    )
    parser.add_argument("--log-odds-mix", action="store_true")
    parser.add_argument(
        "--typed-key-profile",
        choices=("base", "rich", "richpos"),
        default="base",
        help="typed retrieval key family used by the SRSTC retrieval table",
    )
    parser.add_argument("--byte-prior-blend-ppm", type=int, default=0)
    parser.add_argument("--copy-channel-enabled", action="store_true")
    parser.add_argument("--copy-channel-as-band", action="store_true")
    parser.add_argument("--copy-channel-blend-ppm", type=int, default=0)
    parser.add_argument("--copy-channel-cap-entries", type=int, default=100_000)
    parser.add_argument("--copy-channel-top-k", type=int, default=8)
    parser.add_argument("--copy-channel-min-support", type=int, default=4)
    parser.add_argument("--copy-channel-offsets", default="0,-1,1")
    args = parser.parse_args()

    data = args.input.read_bytes()
    if args.limit_bytes > 0:
        data = data[: args.limit_bytes]
    try:
        copy_offsets = parse_copy_offsets(args.copy_channel_offsets)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    config = SrstcConfig(
        expert_mode=args.expert_mode,
        typed_key_profile=args.typed_key_profile,
        log_odds_mix=args.log_odds_mix,
        byte_prior_blend_ppm=args.byte_prior_blend_ppm,
        copy_channel_enabled=args.copy_channel_enabled,
        copy_channel_as_band=args.copy_channel_as_band,
        copy_channel_blend_ppm=args.copy_channel_blend_ppm,
        copy_channel_cap_entries=args.copy_channel_cap_entries,
        copy_channel_top_k=args.copy_channel_top_k,
        copy_channel_min_support=args.copy_channel_min_support,
        copy_channel_offsets=copy_offsets,
    )
    archive = compress(data, config)
    restored = decompress(archive, config)
    ok = restored == data
    receipt = {
        "receipt_type": "srstc_codec_roundtrip",
        "input": str(args.input),
        "input_bytes": len(data),
        "input_sha256": hashlib.sha256(data).hexdigest(),
        "archive_bytes": len(archive),
        "archive_sha256": hashlib.sha256(archive).hexdigest(),
        "roundtrip_ok": ok,
        "bits_per_byte": (len(archive) * 8 / len(data)) if data else 0.0,
        "codec": "streaming_retrieval_codec.py",
        "config": {
            "expert_mode": config.expert_mode,
            "typed_key_profile": config.typed_key_profile,
            "log_odds_mix": config.log_odds_mix,
            "byte_prior_blend_ppm": config.byte_prior_blend_ppm,
            "copy_channel_enabled": config.copy_channel_enabled,
            "copy_channel_as_band": config.copy_channel_as_band,
            "copy_channel_blend_ppm": config.copy_channel_blend_ppm,
            "copy_channel_cap_entries": config.copy_channel_cap_entries,
            "copy_channel_top_k": config.copy_channel_top_k,
            "copy_channel_min_support": config.copy_channel_min_support,
            "copy_channel_offsets": list(config.copy_channel_offsets),
        },
    }
    if args.archive_out:
        args.archive_out.parent.mkdir(parents=True, exist_ok=True)
        args.archive_out.write_bytes(archive)
    if args.receipt_out:
        args.receipt_out.parent.mkdir(parents=True, exist_ok=True)
        args.receipt_out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
