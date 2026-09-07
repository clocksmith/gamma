#!/usr/bin/env python3
"""Bounded synthetic field-state diagnostic; never calls either codec.

The retained implementation is authenticated before loading its definitions.
This tests a source-level opportunity, not a compression or resource claim.
"""
import hashlib
import json
import lzma
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCES = {
    "opcode_typed_anchor_bitmix_v1": "3e9c9ed25997ad10bac94575fb3da5009530ba04fa961da14a016fe89eec9a15",
    "opcode_typed_anchor_ppm_o5_v1": "8a7c54697b71fefdb87f672636365df11b960bbbc9cb7e09dd8b0fd7eb6fe441",
}
FIXTURES = [
    (b"<title>", 1), (b"<id>", 2), (b"<timestamp>", 3),
    (b"<username>", 4), (b"<comment>", 5),
    (b'<text xml:space="preserve">', 6),
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def run():
    tables, bindings = {}, []
    for candidate, expected in SOURCES.items():
        path = ROOT / "programs" / candidate / "p"
        packed = path.read_bytes()
        assert len(packed) < 8192 and sha(packed) == expected
        decoder = lzma.LZMADecompressor(format=lzma.FORMAT_ALONE)
        source = decoder.decompress(packed, max_length=65536)
        assert decoder.eof and not decoder.unused_data
        namespace = {"__name__": "authenticated_field_diagnostic"}
        exec(compile(source, str(path), "exec"), namespace)
        rows = []
        for raw, expected_field in FIXTURES:
            transformed = namespace["oe"](raw)
            inverse = namespace["od"](transformed)
            assert inverse == raw
            raw_state, modeled_state = namespace["GST"](), namespace["GST"]()
            for byte in raw:
                raw_state.up(byte)
            for byte in transformed:
                modeled_state.up(byte)
            assert raw_state.f == expected_field and modeled_state.f == 0
            rows.append({"raw_hex": raw.hex(), "transformed_hex": transformed.hex(),
                         "raw_field": raw_state.f, "modeled_field": modeled_state.f,
                         "exact_opcode_inverse": True})
        # Literal escape and malformed markup retain their exact original bytes.
        exceptions = [b"\x00<title>Oak\x00</title>\xff", b"<title", b"<TITLE>", b"\xff\xfe"]
        for raw in exceptions:
            assert namespace["od"](namespace["oe"](raw)) == raw
        tables[candidate] = {"field_checks": rows, "exception_inverse_checks": len(exceptions)}
        bindings.append({"path": str(path.relative_to(ROOT)), "bytes": len(packed),
                         "sha256": expected, "expanded_source_sha256": sha(source)})
    return {
        "schema": "gamma.enwiki9.opcode-field-state-synthetic-diagnostic.v1",
        "source_bindings": bindings, "table": tables,
        "synthetic_checks": 20, "corpus_executed": False,
        "codec_compress_or_decompress_called": False,
        "objective_credit_bytes": 0, "compression_gain_bytes": None,
        "conclusion": "Both retained implementations recognize six raw opening fields but recognize none after their own opcode conversion. Exact opcode inversion is preserved. This supports testing semantic state driven by decoded literals; it does not establish compression benefit.",
        "limitations": [
            "Synthetic parser state only; no corpus opportunity count or new archive.",
            "Any successor must preserve modeled-byte history and independently prove causal semantic-state updates, inversion, repeatability and complete costs.",
            "Existing source uses runtime floating-point lookup initialization; this diagnostic does not certify cross-host replay.",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
