"""Bounded synthetic performance check with exact predecessor packet comparison."""
import argparse, gc, hashlib, importlib.util, json, platform, random, statistics, subprocess, sys, tempfile, time
from pathlib import Path

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
parser=argparse.ArgumentParser()
parser.add_argument('--baseline-ref',default='5589e95a1e72fb77aafc9db00b2fea90a82ff466')
args=parser.parse_args()
relative=str((HERE/'codec.py').relative_to(ROOT))
baseline=subprocess.run(['git','show',f'{args.baseline_ref}:{relative}'],cwd=ROOT,
                        capture_output=True,check=True,timeout=20).stdout
with tempfile.TemporaryDirectory() as temporary:
    path=Path(temporary)/'codec.py';path.write_bytes(baseline)
    old=load('fragment_before',path)
new=load('fragment_after',HERE/'codec.py')
rng=random.Random(20261110)
tokens=['const ', 'let ', 'if (', 'while (', 'return ', 'for (', 'function ', 'def ', 'in ', 'range(', 'len(', '.length', '.push(', ' = ', ' + ', ' < ', '):\n', ';\n', '    ', 'x', 'y', 'count', 'values', '0', '1', ')', '}', '{', '[', ']', 'é', '🙂']
corpus=[''.join(rng.choice(tokens) for _ in range(384)) for _ in range(24)]
fragments=list(dict.fromkeys(tokens+[''.join(rng.choices(tokens,k=2)) for _ in range(1000)]))
fragments=[s for s in fragments if len(s)>=2]
rows=[]
for width in (6,7,8):
    words=fragments[:(1<<width)-1]
    original=[old.encode(s,words,width) for s in corpus]
    prepared=new.FragmentEncoder(words,width)
    successor=[prepared.encode(s) for s in corpus]
    assert [old.packet_bytes(p) for p in original]==[new.packet_bytes(p) for p in successor]
    for a,b in zip(original,successor):assert vars(a)==vars(b)
    timings={'before':[],'indexed_reused':[]}
    for trial in range(3):
        for name in (['before','indexed_reused'] if trial%2==0 else ['indexed_reused','before']):
            gc.collect();start=time.perf_counter()
            result=[old.encode(s,words,width) for s in corpus] if name=='before' else [prepared.encode(s) for s in corpus]
            timings[name].append(time.perf_counter()-start)
    med={k:statistics.median(v) for k,v in timings.items()}
    rows.append(dict(width=width,programs=len(corpus),source_bytes=sum(len(s.encode()) for s in corpus),packet_bit_identity=True,seconds=timings,median_seconds=med,speedup=med['before']/med['indexed_reused']))
print(json.dumps(dict(baseline_ref=args.baseline_ref,baseline_codec_sha256=hashlib.sha256(baseline).hexdigest(),candidate_codec_sha256=hashlib.sha256((HERE/'codec.py').read_bytes()).hexdigest(),scope='Synthetic mixed programming-fragment microbenchmark, not solver or full-corpus latency',seed=20261110,python=sys.version,platform=platform.platform(),corpus_sha256=hashlib.sha256(json.dumps(corpus,ensure_ascii=False).encode()).hexdigest(),rows=rows),indent=2))
