#!/usr/bin/env python3
"""Price a fixed hindsight context-instruction family; this is not a codec."""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

ORDER = 6


def choose(counts, frequencies, total):
    n = sum(counts.values())
    base = -math.fsum(c * math.log2(frequencies[b] / total) for b, c in counts.items())
    # One first-occurrence flag for every context; active instructions add 12 bits.
    best = (base + 1, 0, 0, base)
    for b, m in counts.items():
        p = frequencies[b] / total
        optimum = max(0.0, min(15.0, 16 * (m / n - p) / (1 - p)))
        for k in sorted({int(math.floor(optimum)), int(math.ceil(optimum))}):
            if not k:
                continue
            a = k / 16
            loss = base - (n - m) * math.log2(1 - a) - m * math.log2((p + a * (1 - p)) / p)
            row = (loss + 13, b, k, loss)
            if row[:3] < best[:3]:
                best = row
    return best[1], best[2], best[3], base


def direct(counts, frequencies, total, b, k):
    return -math.fsum(c * math.log2(((16-k)*frequencies[v] + (k*total if v == b else 0)) / (16*total)) for v,c in counts.items())


def self_test():
    frequencies = [1] * 256
    frequencies[0] = 70
    frequencies[1] = 30
    total = sum(frequencies)
    for counts in [Counter({0: 20}), Counter({0: 2, 1: 2, 254: 12}), Counter(range(256))]:
        b,k,loss,base = choose(counts,frequencies,total)
        brute = min([(direct(counts,frequencies,total,0,0)+1,0,0)] + [(direct(counts,frequencies,total,v,j)+13,v,j) for v in counts for j in range(1,16)])
        assert abs(loss-direct(counts,frequencies,total,b,k)) < 1e-9
        assert abs((loss+(13 if k else 1))-brute[0]) < 1e-9
        assert sum((16-k)*f+(k*total if v==b else 0) for v,f in enumerate(frequencies)) == 16*total
    return True


def screen(data, output):
    global_counts = Counter(data)
    frequencies = [global_counts[b]+1 for b in range(256)]
    total = sum(frequencies)
    contexts = {}
    for i,b in enumerate(data):
        key = data[max(0,i-ORDER):i]
        row = contexts.get(key)
        if row is None:
            contexts[key] = Counter({b:1})
        else:
            row[b] += 1
    encoded = bytearray(struct.pack('<QQ256I',len(data),0,*frequencies))
    accumulator = used = descriptor_bits = active = 0
    losses = []; globals_ = []; rotated = []
    witness = hashlib.sha256()
    def bits(value,count):
        nonlocal accumulator,used,descriptor_bits
        accumulator=(accumulator<<count)|value;used+=count;descriptor_bits+=count
        while used>=8:
            used-=8;encoded.append((accumulator>>used)&255)
        accumulator &= (1<<used)-1
    for key,counts in contexts.items():
        b,k,loss,base = choose(counts,frequencies,total)
        bits(bool(k),1)
        if k:
            bits(b,8);bits(k,4);active+=1
        losses.append(loss);globals_.append(base)
        rotated.append(direct(counts,frequencies,total,(b+1)%256,k))
        witness.update(bytes([len(key)])+key+bytes([b,k]))
    if used:encoded.append(accumulator<<(8-used))
    struct.pack_into('<Q', encoded, 8, descriptor_bits)
    assert struct.unpack_from('<QQ256I', encoded) == (len(data), descriptor_bits, *frequencies)
    # Independently reconstruct every instruction from the charged model bytes.
    cursor=1040*8;decoded=hashlib.sha256()
    def read(count):
        nonlocal cursor
        value=0
        for _ in range(count):
            value=(value<<1)|((encoded[cursor//8]>>(7-cursor%8))&1);cursor+=1
        return value
    for key in contexts:
        present=read(1);b=read(8) if present else 0;k=read(4) if present else 0
        decoded.update(bytes([len(key)])+key+bytes([b,k]))
    assert witness.digest()==decoded.digest() and cursor==1040*8+descriptor_bits
    model=output.with_suffix('.model');model.write_bytes(encoded)
    payload=math.fsum(losses)/8
    priced=payload+len(encoded)
    result=dict(schema='gamma.enwiki9.paid-context-instruction-screen.v1',
        scope='Complete retained opening-10M WRT store, including its five-byte header',
        raw_population='[0, 10000000)',wrt_bytes=len(data),input_sha256=hashlib.sha256(data).hexdigest(),
        order=ORDER,contexts=len(contexts),active_instructions=active,descriptor_bits=descriptor_bits,
        model_bytes=len(encoded),model_sha256=hashlib.sha256(encoded).hexdigest(),model_instruction_roundtrip=True,
        prototype_probabilities='((16-k)*(global_count[b]+1) + k*total*[b=favored]) / (16*total), k in 0..15',
        global_ideal_bytes=math.fsum(globals_)/8,payload_ideal_bytes=payload,
        rotated_payload_ideal_bytes=math.fsum(rotated)/8,priced_ideal_bytes=priced,
        parent_archive_bytes=1634500,parent_program_bytes=261125,parent_counted_10m_bytes=1895625,
        optimistic_gain_over_parent_archive=1634500-priced,
        optimistic_gain_over_counted_parent=1895625-priced,
        target_density_screen_bytes=193893.23,
        target_density_note='Planning screen: 19389323-byte forecast debt / 100; not a full-corpus extrapolation or statistical guarantee.',
        numerical_tolerance_bytes=0.01,numerical_method='binary64 log2 and fsum; diagnostic model cost, not a certified universal lower bound',
        actual_archive_bytes=None,exact_corpus_inverse=None,complete_package_bytes=None,full_corpus_score_bytes=None,objective_credit_bytes=0,
        excluded_costs=['entropy coder termination','candidate source and interpreter','WRT frontend, dictionary and inverse dependencies'],
        verdict='reject this fixed representation on the retained sample' if priced>1895625+0.01 else 'priced likelihood passes optimistic screen; finite codec and complete package still required')
    output.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['priced_ideal_bytes','optimistic_gain_over_counted_parent','verdict']}))


if __name__=='__main__':
    assert self_test()
    if len(sys.argv)>1 and sys.argv[1]=='--self-test':
        print('Exact prototype normalization, exhaustive discrete optimum and direct-loss checks pass')
    else:
        screen(Path(sys.argv[1]).read_bytes(),Path(sys.argv[2]))
