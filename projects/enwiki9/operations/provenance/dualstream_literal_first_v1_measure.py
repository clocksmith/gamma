#!/usr/bin/env python3
"""Retain bounded synthetic codec measurements; never read corpus inputs."""
import hashlib
import json
import os
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests"))
from test_dualstream_literal_first_v1 import codec, fixture, parent


def ref(path):
    data = (ROOT / path).read_bytes()
    return dict(path=path, bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def main():
    os.sched_setaffinity(0, {2})
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2, 512 * 1024**2))
    resource.setrlimit(resource.RLIMIT_CPU, (60, 120))
    resource.setrlimit(resource.RLIMIT_FSIZE, (32 * 1024**2, 32 * 1024**2))
    directory = ROOT / sys.argv[1]
    directory.mkdir(parents=True, exist_ok=False)
    sources = [ref(path) for path in ("tools/dualstream_literal_first_v1.py", "tools/dualstream_grammar_v1.py",
               "tests/test_dualstream_literal_first_v1.py", "operations/provenance/dualstream_literal_first_v1_measure.py")]
    rows = []
    for label, raw in (("shared250k", (fixture(120, 180) * 6)[:250000]),
                       ("arbitrary65536", __import__("random").Random(459).randbytes(65536))):
        (directory / (label + ".raw")).write_bytes(raw)
        baseline = parent(raw)
        (directory / (label + ".P.d2g")).write_bytes(baseline)
        for mode in ("K", "D"):
            begin, cpu = time.monotonic(), time.process_time()
            archive, report = codec.encode(raw, mode)
            encode_cpu, encode_wall = time.process_time() - cpu, time.monotonic() - begin
            (directory / (label + "." + mode + ".d2g")).write_bytes(archive)
            begin, cpu = time.monotonic(), time.process_time()
            decoded, decoder = codec.decode(archive)
            decode_cpu, decode_wall = time.process_time() - cpu, time.monotonic() - begin
            (directory / (label + "." + mode + ".restored.raw")).write_bytes(decoded)
            repeat, repeated = codec.encode(decoded, mode)
            (directory / (label + "." + mode + ".repeat.d2g")).write_bytes(repeat)
            assert decoded == raw and repeat == archive and repeated == report
            assert len(archive) <= len(baseline) and (mode != "K" or archive == baseline)
            row = dict(fixture=label, mode=mode, raw_bytes=len(raw), raw_sha256=hashlib.sha256(raw).hexdigest(),
                       archive_bytes=len(archive), parent_bytes=len(baseline), saved_bytes=len(baseline) - len(archive),
                       exact_inverse=True, raw_discovery_repeat=True, encoder_report=report, decoder_report=decoder,
                       encode_cpu_seconds=encode_cpu, encode_elapsed_seconds=encode_wall,
                       decode_cpu_seconds=decode_cpu, decode_elapsed_seconds=decode_wall,
                       peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
            rows.append(row)
    assert sources == [ref(row["path"]) for row in sources]
    receipt = dict(schema="gamma.enwiki9.literal-first-synthetic-kernel.v1", corpus_executed=False,
                   source_bindings=sources, rows=rows, cpu_affinity=sorted(os.sched_getaffinity(0)),
                   address_limit_bytes=512 * 1024**2, cpu_soft_stop_seconds=60, cpu_hard_stop_seconds=120,
                   file_limit_bytes=32 * 1024**2, complete_package_bytes=None, full_corpus_score_bytes=None)
    (directory / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    entries = [ref(str(p.relative_to(ROOT))) for p in sorted(directory.iterdir()) if p.is_file()]
    (directory / "artifacts.json").write_text(json.dumps(dict(files=entries), indent=2, sort_keys=True) + "\n")
    print(json.dumps(dict(rows=[{k:v for k,v in row.items() if k not in ("encoder_report", "decoder_report")}
                               for row in rows], receipt=str(directory.relative_to(ROOT) / "receipt.json"))))


if __name__ == "__main__":
    main()
