"""Exact integer certificate for the closed elision opportunity; no fitting."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import resource
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lib.fx2_wrt_elision_v1 import Grammar
from tools.fx2_final_counts_replay_v1 import framing


def reference(path):
    data = path.read_bytes()
    return dict(path=str(path.relative_to(ROOT)), bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def bound(histogram):
    product = 1; n = 0
    for count, occurrences in sorted(histogram.items()):
        if not 1 <= count <= 65535 or occurrences < 1:
            raise ValueError('invalid truth-count histogram')
        product *= pow(count, occurrences); n += occurrences
    exponent = 16*n
    if product & (product-1) == 0:
        exact = exponent-(product.bit_length()-1)
        lower = upper = exact
    else:
        lower = exponent-product.bit_length(); upper = lower+1
        # Strict rational inequalities; no logarithm evaluation or floats.
        assert product > (1 << (exponent-upper))
        assert product < (1 << (exponent-lower))
    packed = product.to_bytes((product.bit_length()+7)//8, 'little')
    return dict(events=n, probability_denominator_exponent=exponent,
                product_bit_length=product.bit_length(), product_sha256=hashlib.sha256(packed).hexdigest(),
                lower_bits=lower, upper_bits=upper, exact=lower == upper,
                inequality='equal' if lower == upper else 'strict at both endpoints',
                truth_count_histogram=[[c,k] for c,k in sorted(histogram.items())])


def main():
    if len(sys.argv) != 3: raise ValueError('expected closed result directory and new output')
    resource.setrlimit(resource.RLIMIT_AS, (512*1024**2, 512*1024**2))
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    for hist, low, high in [({},0,0),({32768:3},3,3),({65535:1},0,1),({1:2},32,32)]:
        r = bound(hist); assert (r['lower_bits'],r['upper_bits']) == (low,high)
    out = ROOT/sys.argv[1]; target = ROOT/sys.argv[2]
    counts_path = out/'parent.q16'; body_path = out/'D-decode.modeled'; prefix_path = out/'prefix.bin'
    metadata_path = out/'projection.json'; decision_path = out/'decision.json'
    if counts_path.stat().st_size > 16000000 or body_path.stat().st_size > 1000000:
        raise ValueError('audit population bound')
    counts = counts_path.read_bytes(); body = body_path.read_bytes(); metadata = json.loads(metadata_path.read_text())
    decision = json.loads(decision_path.read_text())
    if decision['status'] != 'passed' or len(counts) != 16*len(body): raise ValueError('unclosed population')
    if hashlib.sha256(counts).hexdigest() != metadata['parent_count_sha256']:
        raise ValueError('counts differ')
    if hashlib.sha256(body).hexdigest() != metadata['modeled_sha256']:
        raise ValueError('decoded input differs')
    _, vocab = framing(prefix_path.read_bytes(), len(body)); model = Grammar(metadata['word_count'], vocab)
    histograms = {'V': Counter(), 'D': Counter()}; hashes = {a:hashlib.sha256() for a in histograms}
    for i, (count,) in enumerate(struct.iter_unpack('<H', counts)):
        fv = model.forced(False); fd = model.forced(True)
        y = body[i//8] >> (7-i%8) & 1
        if fv is not None and fv != fd: raise ValueError('constraint containment differs')
        for a, forced in [('V',fv),('D',fd)]:
            if forced is not None:
                if forced != y: raise ValueError('unsound forced bit')
                c = count if y else 65536-count
                histograms[a][c] += 1; hashes[a].update(struct.pack('<QHB',i,count,y))
        model.observe(y)
    model.finish(); arms = {}
    for a in histograms:
        arms[a] = bound(histograms[a]); arms[a]['event_sha256'] = hashes[a].hexdigest()
        if arms[a]['events'] != decision['arms'][a]['elided_events']: raise ValueError('omission population differs')
    result = dict(schema='gamma.enwiki9.exact-elision-certificate.v1', arms=arms,
        identity='F=16*N-log2(product(c_truth)); integer product bounds establish the reported endpoints.',
        scope='Only the declared omitted events on this fixed parent trajectory. It is not a finite archive, package or full-corpus bound.',
        fitting=False, objective_credit_bytes=0,
        evidence=[reference(p) for p in [counts_path,body_path,prefix_path,metadata_path,decision_path,
                    ROOT/'lib/fx2_wrt_elision_v1.py',Path(__file__).resolve()]])
    with target.open('x') as f: json.dump(result,f,indent=2,sort_keys=True); f.write('\n')
    print(json.dumps({a:{k:r[k] for k in ['events','lower_bits','upper_bits','exact']} for a,r in arms.items()}))


if __name__ == '__main__': main()
