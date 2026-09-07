#!/usr/bin/env python3
"""Bounded synthetic FIFO-permutation kernels; no corpus access."""
import hashlib
import json
import os
from pathlib import Path
import random
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import causal_bucket_v1 as codec


def main():
    os.sched_setaffinity(0, {2})
    resource.setrlimit(resource.RLIMIT_AS, (536870912, 536870912))
    resource.setrlimit(resource.RLIMIT_CPU, (60, 120))
    dest = ROOT / sys.argv[1]
    dest.mkdir(parents=True, exist_ok=False)
    sources = []
    for path in ["tools/causal_bucket_v1.py", "tools/dualstream_grammar_v1.py", "operations/provenance/causal_bucket_v1_measure.py"]:
        data = (ROOT / path).read_bytes()
        sources.append(dict(path=path, bytes=len(data), sha256=hashlib.sha256(data).hexdigest()))
        target = dest / "source" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    rng, value, walk = random.Random(871), 0, bytearray()
    for _ in range(8192):
        value = (value + rng.choice([-1, 0, 1])) % 256
        walk.append(value)
    rows = []
    for label, raw in [("walk8192", bytes(walk)), ("random2048", random.Random(491).randbytes(2048))]:
        (dest / (label + ".raw")).write_bytes(raw)
        plain = codec.HEADER.pack(codec.PLAIN_MAGIC, 65536, 1, len(raw)) + codec.base.frame_bytes(raw, "plain")[0]
        (dest / (label + ".P.d2g")).write_bytes(plain)
        for mode in ["K", "D"]:
            start, cpu = time.monotonic(), time.process_time()
            archive, report = codec.encode(raw, mode)
            enc = dict(cpu_seconds=time.process_time() - cpu, elapsed_seconds=time.monotonic() - start)
            start, cpu = time.monotonic(), time.process_time()
            inverse, decoder = codec.decode(archive)
            dec = dict(cpu_seconds=time.process_time() - cpu, elapsed_seconds=time.monotonic() - start)
            repeat, repeated = codec.encode(inverse, mode)
            assert inverse == raw and archive == repeat and report == repeated
            assert mode != "K" or archive == plain
            common = {k:v for k,v in report.items() if k != "mode"}
            common["frames"] = [{k:v for k,v in f.items() if k != "comparison"} for f in report["frames"]]
            assert common == decoder
            for suffix, data in [(".d2g", archive), (".repeat.d2g", repeat), (".restored.raw", inverse)]:
                (dest / (label + "." + mode + suffix)).write_bytes(data)
            rows.append(dict(fixture=label, mode=mode, raw_bytes=len(raw), parent_bytes=len(plain), archive_bytes=len(archive),
                             exact_inverse=True, raw_repeat=True, common_decoder_equal=True, encode=enc, decode=dec,
                             peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, report=report))
    for row in sources:
        assert hashlib.sha256((ROOT / row["path"]).read_bytes()).hexdigest() == row["sha256"]
    result = dict(schema="gamma.enwiki9.causal-bucket-kernels.v1", synthetic_only=True, corpus_executed=False,
                  sources=sources, rows=rows, transform_spec=codec.TRANSFORM_SPEC,
                  limits=dict(cpus=[2], address_bytes=536870912, cpu_soft_seconds=60, cpu_hard_seconds=120),
                  complete_package_bytes=None, full_corpus_score_bytes=None)
    (dest / "receipt.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    entries = [dict(path=str(p.relative_to(ROOT)), bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest())
               for p in sorted(dest.rglob("*")) if p.is_file()]
    (dest / "index.json").write_text(json.dumps(dict(files=entries), indent=2, sort_keys=True) + "\n")
    print(json.dumps([{k:v for k,v in row.items() if k != "report"} for row in rows]))


if __name__ == "__main__":
    main()
