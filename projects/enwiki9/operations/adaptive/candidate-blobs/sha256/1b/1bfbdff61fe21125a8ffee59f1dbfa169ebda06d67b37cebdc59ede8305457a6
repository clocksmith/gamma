#!/usr/bin/env python3
"""Derive an A-opportunity manifest emitter from the frozen dual-clock scan."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


EXPECTED_SOURCE_SHA256 = (
    "ff08edea191055ceecc23ebf6008e1aaa2f0f573c1a005b61d6a48c45be68b8a"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


MANIFEST_SUPPORT = r'''
FILE* horizon_manifest = nullptr;
uint64_t horizon_manifest_rows = 0;

void PutLe64(uint8_t* output, uint64_t value) {
  for (unsigned int index = 0; index < 8; ++index) {
    output[index] = static_cast<uint8_t>(value >> (8U * index));
  }
}

void StartManifest(const char* path) {
  horizon_manifest = std::fopen(path, "wb+");
  if (horizon_manifest == nullptr) Fail("open manifest");
  std::setvbuf(horizon_manifest, nullptr, _IOFBF, 1U << 20);
  std::array<uint8_t, 32> header{};
  const std::array<uint8_t, 8> magic{{'G','H','O','R','A','1',0,0}};
  std::copy(magic.begin(), magic.end(), header.begin());
  PutLe64(header.data() + 16, kStreamBytes);
  PutLe64(header.data() + 24, 13ULL);
  if (std::fwrite(header.data(), 1, header.size(), horizon_manifest) !=
      header.size()) Fail("write manifest header");
}

void WriteManifest(uint64_t coordinate, uint8_t donor, uint8_t shifted,
                   uint8_t random, uint8_t negated, uint8_t truth) {
  std::array<uint8_t, 13> row{};
  PutLe64(row.data(), coordinate);
  row[8] = donor;
  row[9] = shifted;
  row[10] = random;
  row[11] = negated;
  row[12] = truth;
  if (std::fwrite(row.data(), 1, row.size(), horizon_manifest) != row.size()) {
    Fail("write manifest row");
  }
  ++horizon_manifest_rows;
}

void FinishManifest() {
  if (std::fflush(horizon_manifest) != 0 ||
      std::fseek(horizon_manifest, 8, SEEK_SET) != 0) {
    Fail("seek manifest count");
  }
  std::array<uint8_t, 8> count{};
  PutLe64(count.data(), horizon_manifest_rows);
  if (std::fwrite(count.data(), 1, count.size(), horizon_manifest) !=
          count.size() ||
      std::fclose(horizon_manifest) != 0) {
    Fail("close manifest");
  }
  horizon_manifest = nullptr;
}
'''.strip()


def materialize(source: Path, output: Path) -> dict[str, object]:
    if sha256(source) != EXPECTED_SOURCE_SHA256:
        raise RuntimeError("frozen HORIZON transition source identity mismatch")
    if output.exists():
        raise FileExistsError(output)
    text = source.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "struct Candidate { bool active=false; uint64_t coordinate=0; uint8_t donor=0; };",
        "struct Candidate { bool active=false; uint64_t coordinate=0; uint8_t donor=0; };\n\n"
        + MANIFEST_SUPPORT,
        "manifest support",
    )
    text = replace_once(
        text,
        "    const bool n = negated == truth;\n"
        "    ++arm->active; arm->d += d; arm->s += s; arm->r += r; arm->n += n;",
        "    const bool n = negated == truth;\n"
        "    if (id == 'A') {\n"
        "      WriteManifest(current, candidate.donor, shifted, random, negated, truth);\n"
        "    }\n"
        "    ++arm->active; arm->d += d; arm->s += s; arm->r += r; arm->n += n;",
        "A manifest row",
    )
    text = replace_once(
        text,
        "int main(int argc,char** argv) {\n"
        "  if(argc!=3){std::fprintf(stderr,\"usage: %s ENDPOINT_STORE OUTPUT_JSON\\n\",argv[0]);return 64;}",
        "int main(int argc,char** argv) {\n"
        "  if(argc!=4){std::fprintf(stderr,\"usage: %s ENDPOINT_STORE OUTPUT_JSON OUTPUT_MANIFEST\\n\",argv[0]);return 64;}\n"
        "  StartManifest(argv[3]);",
        "manifest arguments",
    )
    text = replace_once(
        text,
        "  scanner.Finish(); if(close(input)!=0) Fail(\"close input\"); WriteReceipt(argv[2],scanner);\n"
        "  return 0;",
        "  scanner.Finish(); if(close(input)!=0) Fail(\"close input\"); WriteReceipt(argv[2],scanner);\n"
        "  FinishManifest();\n"
        "  return 0;",
        "manifest finalization",
    )
    output.write_text(text, encoding="utf-8")
    return {
        "schema": "gamma.enwiki9.horizon-a-manifest-materialization.v1",
        "source": str(source.resolve()),
        "source_sha256": EXPECTED_SOURCE_SHA256,
        "output": str(output.resolve()),
        "output_sha256": sha256(output),
        "manifest_magic": "GHORA1\\0\\0",
        "manifest_record_bytes": 13,
        "scientific_transition_change": False,
        "score_credit_bytes": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()
    receipt = materialize(args.source.resolve(), args.output.resolve())
    args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
