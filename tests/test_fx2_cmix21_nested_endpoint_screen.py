from __future__ import annotations

import json
import struct
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "projects/enwiki9/tools/fx2_cmix21_nested_endpoint_screen.cpp"


class CmixRangeEncoder:
    def __init__(self) -> None:
        self.x1 = 0
        self.x2 = 0xFFFFFFFF
        self.output = bytearray()

    def encode(self, bit: int, p1: int) -> None:
        span = (self.x2 - self.x1) & 0xFFFFFFFF
        xmid = (
            self.x1
            + (span >> 16) * p1
            + (((span & 0xFFFF) * p1) >> 16)
        ) & 0xFFFFFFFF
        if bit:
            self.x2 = xmid
        else:
            self.x1 = (xmid + 1) & 0xFFFFFFFF
        self._normalize()

    def _normalize(self) -> None:
        while ((self.x1 ^ self.x2) & 0xFF000000) == 0:
            self.output.append(self.x2 >> 24)
            self.x1 = (self.x1 << 8) & 0xFFFFFFFF
            self.x2 = ((self.x2 << 8) + 255) & 0xFFFFFFFF

    def finish(self) -> bytes:
        self._normalize()
        self.output.append(self.x2 >> 24)
        return bytes(self.output)


def build_tool(tmp_path: Path) -> Path:
    binary = tmp_path / "nested-screen"
    subprocess.run(
        [
            "g++",
            "-std=c++17",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            str(SOURCE),
            "-o",
            str(binary),
        ],
        check=True,
    )
    return binary


def write_synthetic_trace(path: Path) -> tuple[list[int], list[int]]:
    rows = 800
    endpoint_count = 6
    layer0_count = 1
    row_bytes = 1 + 2 * endpoint_count
    bits: list[int] = []
    base: list[int] = []
    with path.open("wb") as f:
        f.write(
            struct.pack(
                "<8sIIIIIQ",
                b"CMNEST1\0",
                1,
                36,
                row_bytes,
                endpoint_count,
                layer0_count,
                rows,
            )
        )
        for row in range(rows):
            bit = ((row * 17 + row // 7) & 3) != 0
            bit = int(bit)
            base_p1 = 43000 if bit else 22500
            # Endpoint 5 is a strong causal-looking endpoint throughout all
            # splits. Other endpoints are neutral or harmful.
            endpoint = 56000 if bit else 9500
            probabilities = [
                base_p1,
                32768,
                32768,
                65535 - base_p1,
                32768,
                endpoint,
            ]
            f.write(struct.pack("<B6H", bit, *probabilities))
            bits.append(bit)
            base.append(base_p1)
    return bits, base


def write_base_archive(path: Path, bits: list[int], probabilities: list[int]) -> None:
    coder = CmixRangeEncoder()
    for bit, p1 in zip(bits, probabilities):
        coder.encode(bit, p1)
    payload = coder.finish()
    transformed_bytes = len(bits) // 8
    header = transformed_bytes.to_bytes(5, "big")
    path.write_bytes(header + payload)


def write_wrt_store(path: Path, bits: list[int]) -> None:
    payload = bytearray()
    for start in range(0, len(bits), 8):
        byte = 0
        for bit in bits[start : start + 8]:
            byte = (byte << 1) | bit
        payload.append(byte)
    path.write_bytes(b"\x80\x00\x00\x00\x00" + payload)


def write_external_endpoint(path: Path, bits: list[int]) -> None:
    with path.open("wb") as f:
        f.write(struct.pack("<8sQ", b"CMX21P1\0", len(bits)))
        for bit in bits:
            f.write(struct.pack("<H", 62000 if bit else 3500))


def test_matched_screen_proves_base_identity_and_decoder_replay(tmp_path: Path) -> None:
    binary = build_tool(tmp_path)
    trace = tmp_path / "trace.bin"
    archive = tmp_path / "base.comp"
    receipt = tmp_path / "receipt.json"
    candidate = tmp_path / "candidate.bin"
    exported_base = tmp_path / "base.p1"
    store = tmp_path / "stream.store"
    external = tmp_path / "teacher.p1"
    bits, probabilities = write_synthetic_trace(trace)
    write_base_archive(archive, bits, probabilities)
    write_wrt_store(store, bits)
    write_external_endpoint(external, bits)

    subprocess.run(
        [
            str(binary),
            "--trace",
            str(trace),
            "--base-archive",
            str(archive),
            "--wrt-store",
            str(store),
            "--base-endpoint-name",
            "synthetic_fx2_base",
            "--external-endpoint",
            str(external),
            "--raw-scope-bytes",
            "100",
            "--top-endpoints",
            "5",
            "--baseline-score-bytes",
            "1000",
            "--target-score-bytes",
            "900",
            "--native-integration-margin-bytes-per-1m",
            "25",
            "--payload-bytes",
            "10",
            "--candidate-payload",
            str(candidate),
            "--export-base-p1",
            str(exported_base),
            "--output",
            str(receipt),
        ],
        check=True,
    )

    result = json.loads(receipt.read_text())
    assert result["base"]["reference_archive_identity"] is True
    assert result["base"]["name"] == "synthetic_fx2_base"
    assert result["base"]["archive_payload_identity"] is True
    assert result["trace"]["wrt_truth_stream_identity"] is True
    assert result["trace"]["endpoint_count"] == 7
    assert result["exact_cmix_replay"]["decoder_replay_ok"] is True
    assert result["exact_cmix_replay"]["holdout_blocks"] == 16
    assert result["exact_cmix_replay"][
        "total_holdout_block_regression_bytes"
    ] >= result["exact_cmix_replay"]["largest_holdout_block_regression_bytes"]
    assert result["selected"]["endpoint"] == 6
    assert result["exact_cmix_replay"]["full_saved_bytes"] > 0
    assert result["promotion_authorized"] is False
    assert result["economics"]["baseline_score_bytes"] == 1000
    assert result["economics"]["target_score_bytes"] == 900
    assert result["economics"]["forecast_debt_bytes_per_1m"] == 0.1
    assert result["economics"][
        "native_integration_margin_bytes_per_1m"
    ] == 25
    assert result["economics"]["payload_bytes"] == 10
    assert candidate.stat().st_size == result["exact_cmix_replay"][
        "candidate_payload_bytes"
    ]
    exported = exported_base.read_bytes()
    assert exported[:8] == b"FX2P1V1\0"
    assert struct.unpack_from("<Q", exported, 8)[0] == len(bits)
    assert list(struct.unpack_from(f"<{len(bits)}H", exported, 16)) == probabilities
    assert result["trace"]["exported_base_p1_path"] == str(exported_base)


def test_matched_screen_rejects_trace_size_mismatch(tmp_path: Path) -> None:
    binary = build_tool(tmp_path)
    trace = tmp_path / "trace.bin"
    archive = tmp_path / "base.comp"
    receipt = tmp_path / "receipt.json"
    bits, probabilities = write_synthetic_trace(trace)
    write_base_archive(archive, bits, probabilities)
    trace.write_bytes(trace.read_bytes()[:-1])

    completed = subprocess.run(
        [
            str(binary),
            "--trace",
            str(trace),
            "--base-archive",
            str(archive),
            "--raw-scope-bytes",
            "100",
            "--output",
            str(receipt),
        ],
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 1
    assert "row count/file size mismatch" in completed.stderr
    assert not receipt.exists()


def test_matched_screen_rejects_observation_archive_drift(tmp_path: Path) -> None:
    binary = build_tool(tmp_path)
    trace = tmp_path / "trace.bin"
    archive = tmp_path / "base.comp"
    reference = tmp_path / "reference.comp"
    receipt = tmp_path / "receipt.json"
    bits, probabilities = write_synthetic_trace(trace)
    write_base_archive(archive, bits, probabilities)
    drifted = bytearray(archive.read_bytes())
    drifted[-1] ^= 1
    reference.write_bytes(drifted)

    completed = subprocess.run(
        [
            str(binary),
            "--trace",
            str(trace),
            "--base-archive",
            str(archive),
            "--reference-archive",
            str(reference),
            "--raw-scope-bytes",
            "100",
            "--output",
            str(receipt),
        ],
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 2
    result = json.loads(receipt.read_text())
    assert result["base"]["reference_archive_identity"] is False
    assert result["verdict"] == "invalid_observation_archive_identity"
