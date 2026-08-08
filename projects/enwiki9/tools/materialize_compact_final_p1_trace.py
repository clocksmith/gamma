#!/usr/bin/env python3
"""Materialize an isolated compact-replacement build with a final-P1 observer."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil


EXPECTED_ENCODER_SHA256 = (
    "a206c7b9542d617dd1a3a4b3be28e8ee29ec4e4419f4a0a18bcd66e0c620e8f1"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


TRACE_SUPPORT = r'''
#include <cstdio>
#include <cstdlib>

#ifndef CMIX_BINARY_P1_TRACE
#define CMIX_BINARY_P1_TRACE 0
#endif

#if CMIX_BINARY_P1_TRACE
namespace {
FILE* binary_p1_trace = nullptr;
unsigned long long binary_p1_trace_rows = 0;

void StartBinaryProbabilityTrace() {
  const char* trace_path = std::getenv("CMIX_P1_TRACE");
  if (trace_path == nullptr || trace_path[0] == '\0') return;
  binary_p1_trace = std::fopen(trace_path, "wb+");
  if (binary_p1_trace == nullptr) {
    std::perror("CMIX_P1_TRACE");
    std::abort();
  }
  std::setvbuf(binary_p1_trace, nullptr, _IOFBF, 1U << 20);
  const unsigned char header[16] = {
      'C', 'M', 'X', '2', '1', 'P', '1', '\0',
      0, 0, 0, 0, 0, 0, 0, 0};
  if (std::fwrite(header, 1, sizeof(header), binary_p1_trace) !=
      sizeof(header)) {
    std::perror("CMIX_P1_TRACE header");
    std::abort();
  }
}

void TraceBinaryProbability(unsigned int probability) {
  if (binary_p1_trace == nullptr) return;
  if (std::fputc(probability & 0xffU, binary_p1_trace) == EOF ||
      std::fputc((probability >> 8) & 0xffU, binary_p1_trace) == EOF) {
    std::perror("CMIX_P1_TRACE row");
    std::abort();
  }
  ++binary_p1_trace_rows;
}

void FinishBinaryProbabilityTrace() {
  if (binary_p1_trace == nullptr) return;
  if (std::fflush(binary_p1_trace) != 0 ||
      std::fseek(binary_p1_trace, 8, SEEK_SET) != 0) {
    std::perror("CMIX_P1_TRACE finalize");
    std::abort();
  }
  unsigned char count[8];
  for (unsigned int index = 0; index < 8; ++index) {
    count[index] = (binary_p1_trace_rows >> (8 * index)) & 0xffU;
  }
  if (std::fwrite(count, 1, sizeof(count), binary_p1_trace) != sizeof(count) ||
      std::fclose(binary_p1_trace) != 0) {
    std::perror("CMIX_P1_TRACE close");
    std::abort();
  }
  binary_p1_trace = nullptr;
}
}  // namespace
#endif
'''.lstrip()


def replace_once(value: str, old: str, new: str, label: str) -> str:
    count = value.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return value.replace(old, new, 1)


def materialize(source: Path, output: Path) -> dict[str, object]:
    if output.exists():
        raise FileExistsError(output)
    encoder_source = source / "src/coder/encoder.cpp"
    if sha256(encoder_source) != EXPECTED_ENCODER_SHA256:
        raise RuntimeError("compact encoder source hash is not the frozen parent")
    shutil.copytree(source, output)

    makefile = output / "Makefile"
    make_text = makefile.read_text()
    make_text = replace_once(
        make_text,
        "\t-DCMIX_USE_PAQ8=0 \\\n",
        "\t-DCMIX_USE_PAQ8=0 \\\n\t-DCMIX_BINARY_P1_TRACE=1 \\\n",
        "Makefile trace define",
    )
    makefile.write_text(make_text)

    encoder = output / "src/coder/encoder.cpp"
    text = encoder.read_text()
    text = replace_once(
        text,
        '#include "encoder.h"\n',
        TRACE_SUPPORT + '#include "encoder.h"\n',
        "encoder trace support",
    )
    text = replace_once(
        text,
        "    x2_(0xffffffff), p_(p) {\n}",
        "    x2_(0xffffffff), p_(p) {\n"
        "#if CMIX_BINARY_P1_TRACE\n"
        "  StartBinaryProbabilityTrace();\n"
        "#endif\n"
        "}",
        "encoder trace initialization",
    )
    text = replace_once(
        text,
        "  const unsigned int p = Discretize(raw_probability);\n",
        "  const unsigned int p = Discretize(raw_probability);\n"
        "#if CMIX_BINARY_P1_TRACE\n"
        "  TraceBinaryProbability(p);\n"
        "#endif\n",
        "encoder trace row",
    )
    text = replace_once(
        text,
        "  WriteByte(x2_ >> 24);\n}\n",
        "  WriteByte(x2_ >> 24);\n"
        "#if CMIX_BINARY_P1_TRACE\n"
        "  FinishBinaryProbabilityTrace();\n"
        "#endif\n"
        "}\n",
        "encoder trace finalization",
    )
    encoder.write_text(text)
    return {
        "schema": "compact_final_p1_trace_materialization_v1",
        "source": str(source.resolve()),
        "output": str(output.resolve()),
        "frozen_encoder_sha256": EXPECTED_ENCODER_SHA256,
        "materialized_encoder_sha256": sha256(encoder),
        "makefile_sha256": sha256(makefile),
        "observer_environment": "CMIX_P1_TRACE",
        "score_credit_bytes": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()
    receipt = materialize(args.source.resolve(), args.output.resolve())
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
