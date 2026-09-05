"""Authenticate public fx2 vocabulary and optional package components without execution."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_BYTES = 96994188
ARCHIVE_SHA256 = "b5330c493ab2d2930469b9bc0d1d2de723ca9e1d660699bcf1be187edc087ae5"
COMPRESSOR_BYTES = 3426642
COMPRESSOR_SHA256 = "eff2f4b0ebd350b49d6b69eadf20de4efb34e7025ad10c13a0dce9763db4e040"
WEIGHTS_SHA256 = "7f4db6c8c843a7e6264b6a48ed4805e9e431f543df7a9a0ecb37a35a5e4b8860"
SOURCE_COMMIT = "83f2603f3f7751da5f429fd32669807eb8510494"


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def authenticate(path: Path) -> dict:
    if path.is_symlink() or path.stat().st_size != ARCHIVE_BYTES or digest(path) != ARCHIVE_SHA256:
        raise ValueError("public archive differs from pinned release asset 540574386")
    with path.open("rb") as stream:
        stream.seek(-16, 2)
        trailer = stream.read(16)
        dictionary_bytes, article_order_bytes, payload_bytes, weights_bytes = struct.unpack("<4i", trailer)
        if min(dictionary_bytes, payload_bytes, weights_bytes) <= 0 or article_order_bytes < 0:
            raise ValueError("public trailer contains invalid segment sizes")
        payload_offset = ARCHIVE_BYTES - 16 - payload_bytes
        weights_offset = payload_offset - weights_bytes
        binary_bytes = weights_offset - dictionary_bytes
        if binary_bytes <= 0 or payload_bytes < 37:
            raise ValueError("public segments overlap or exceed the archive")
        stream.seek(weights_offset)
        weights_digest = hashlib.sha256()
        remaining = weights_bytes
        while remaining:
            block = stream.read(min(1024 * 1024, remaining))
            if not block:
                raise ValueError("truncated embedded weights")
            weights_digest.update(block)
            remaining -= len(block)
        if weights_digest.hexdigest() != WEIGHTS_SHA256:
            raise ValueError("embedded model differs from the pinned runtime model")
        stream.seek(payload_offset)
        header = stream.read(37)
    transformed_bytes = int.from_bytes(bytes([header[0] & 127]) + header[1:5], "big")
    if transformed_bytes < 10000 or not header[0] & 128:
        raise ValueError("payload lacks the expected dictionary and explicit vocabulary")
    bitmap = header[5:37]
    alphabet = [byte for byte in range(256) if bitmap[byte // 8] & (1 << (byte % 8))]
    if len(alphabet) != 205:
        raise ValueError("public model vocabulary is not 205 symbols")
    return {
        "schema": "gamma.enwiki9.public-fx2-authenticated-vocabulary.v1",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_commit": SOURCE_COMMIT,
        "asset": {"id": 540574386, "path": str(path.relative_to(ROOT)),
                  "bytes": ARCHIVE_BYTES, "sha256": ARCHIVE_SHA256,
                  "url": "https://github.com/astOwOlfo/fx2-cmix-transformer-v1/releases/download/binaries/archive9"},
        "layout_authority": ["src/readalike_prepr/self_extract.h:98", "src/readalike_prepr/self_extract.h:186", "src/runner.cpp:330"],
        "trailer_hex": trailer.hex(), "payload_header_hex": header.hex(),
        "dictionary_bytes": dictionary_bytes, "article_order_bytes": article_order_bytes,
        "decompressor_bytes": binary_bytes, "payload_bytes": payload_bytes,
        "payload_offset": payload_offset, "preprocessed_scope_bytes": transformed_bytes,
        "embedded_weights": {"offset": weights_offset, "bytes": weights_bytes, "sha256": weights_digest.hexdigest()},
        "vocabulary_bitmap_hex": bitmap.hex(), "vocabulary_bytes": alphabet,
        "vocabulary_size": len(alphabet), "archive_executed": False,
        "full_corpus_decoded": False, "objective_credit_bytes": 0,
        "authority": "Exact pinned release bytes bind this alphabet to the embedded runtime weights; no codec reproduction or prize acceptance is implied.",
    }


def container_components(path: Path, *, compressor: bool = False) -> dict:
    """Hash contiguous trailer-derived ranges and the complete pinned asset together."""
    expected_bytes = COMPRESSOR_BYTES if compressor else ARCHIVE_BYTES
    expected_sha = COMPRESSOR_SHA256 if compressor else ARCHIVE_SHA256
    asset_id = 540574026 if compressor else 540574386
    name = "cmix" if compressor else "archive9"
    if path.is_symlink() or not path.is_file() or path.stat().st_size != expected_bytes:
        raise ValueError(f"public {name} differs from pinned release asset {asset_id}")
    with path.open("rb") as stream:
        stream.seek(-16, 2)
        trailer = stream.read(16)
        if len(trailer) != 16:
            raise ValueError(f"truncated {name} trailer")
        dictionary, order, payload, weights = struct.unpack("<4i", trailer)
        if min(dictionary, weights) <= 0 or order < 0 or payload < 0:
            raise ValueError(f"invalid {name} segment sizes")
        if (compressor and (payload != 0 or order <= 0)) or (not compressor and payload < 37):
            raise ValueError(f"invalid {name} payload or article-order size")
        # The archive retains the order size in its trailer but has no order segment.
        sizes = [("dictionary", dictionary)]
        sizes += [("article_order", order)] if compressor else []
        sizes += [("weights", weights)]
        sizes += [] if compressor else [("payload", payload)]
        binary = expected_bytes - 16 - sum(size for _, size in sizes)
        if binary <= 0:
            raise ValueError(f"{name} segments overlap or exceed the container")
        sizes = [("binary", binary), *sizes, ("trailer", 16)]
        stream.seek(0)
        complete = hashlib.sha256()
        components = {}
        offset = 0
        for component, size in sizes:
            if size <= 0 or offset < 0 or offset + size > expected_bytes:
                raise ValueError(f"invalid {name} component bounds: {component}")
            component_sha = hashlib.sha256()
            remaining = size
            while remaining:
                block = stream.read(min(1024 * 1024, remaining))
                if not block:
                    raise ValueError(f"truncated {name} component: {component}")
                component_sha.update(block)
                complete.update(block)
                remaining -= len(block)
            components[component] = {"offset": offset, "bytes": size,
                                     "sha256": component_sha.hexdigest()}
            offset += size
        if offset != expected_bytes or stream.read(1) or complete.hexdigest() != expected_sha:
            raise ValueError(f"public {name} differs from pinned release asset {asset_id}")
    if components["trailer"]["sha256"] != hashlib.sha256(trailer).hexdigest():
        raise ValueError(f"{name} trailer changed during authentication")
    if components["weights"]["sha256"] != WEIGHTS_SHA256:
        raise ValueError(f"{name} embedded model differs from the pinned runtime model")
    return {
        "asset": {"id": asset_id, "path": str(path.relative_to(ROOT)),
                  "bytes": expected_bytes, "sha256": complete.hexdigest(),
                  "url": f"https://github.com/astOwOlfo/fx2-cmix-transformer-v1/releases/download/binaries/{name}"},
        "trailer_hex": trailer.hex(), "declared_article_order_bytes": order,
        "components": components, "executed": False,
    }


def authenticate_pair(archive: Path, compressor: Path) -> dict:
    """Extend vocabulary evidence with authenticated binary-package accounting."""
    value = authenticate(archive)
    containers = {"archive": container_components(archive),
                  "compressor": container_components(compressor, compressor=True)}
    for name in ("binary", "dictionary", "weights"):
        left, right = (item["components"][name] for item in containers.values())
        if (left["bytes"], left["sha256"]) != (right["bytes"], right["sha256"]):
            raise ValueError(f"public compressor/archive {name} components differ")
    value.update({
        "containers": containers,
        "equal_components": ["binary", "dictionary", "weights"],
        "compressor_executed": False, "algorithm_credit_bytes": 0,
        "prize_acceptance_verified": False,
        "binary_package_accounting": {
            "formula": "archive bytes + compressor bytes",
            "counted_total_bytes": sum(item["asset"]["bytes"] for item in containers.values()),
            "model_copies_counted": 2,
            "model_bytes_included": sum(item["components"]["weights"]["bytes"] for item in containers.values()),
            "required_option_bytes": None, "complete_prize_score_bytes": None,
            "authority": "Authenticated public file sizes; model copies are already included. Required options, submission eligibility and committee acceptance are not verified.",
        },
    })
    value["layout_authority"] += ["build_and_construct_comp.sh:112-120",
                                  "src/readalike_prepr/self_extract.h:151-172",
                                  "src/readalike_prepr/self_extract.h:212-226",
                                  "src/runner.cpp:1082-1097"]
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--compressor", type=Path, help="Also authenticate the pinned public cmix and count both containers")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    value = (authenticate_pair(args.archive.absolute(), args.compressor.absolute())
             if args.compressor else authenticate(args.archive.resolve()))
    value["authenticator_sha256"] = digest(Path(__file__))
    with args.output.open("x") as output:
        output.write(json.dumps(value, indent=2) + "\n")
    summary = {"vocabulary_size": value["vocabulary_size"], "embedded_weights_match": True,
               "archive_executed": False, "output": str(args.output)}
    if args.compressor:
        summary.update({"counted_total_bytes": value["binary_package_accounting"]["counted_total_bytes"],
                        "compressor_executed": False, "algorithm_credit_bytes": 0})
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
