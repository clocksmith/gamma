"""Canonical packet construction and exact paid costs; search never uses min-F."""
from collections import Counter
import hashlib
import math
from pathlib import Path
import statistics
import struct
import common as c


def distribution(values):
    values=sorted(values);assert values
    return {'n':len(values),'total':sum(values),'median':statistics.median(values),
            'p90':values[math.ceil(.9*len(values))-1],'p95':values[math.ceil(.95*len(values))-1],
            'worst':values[-1],'within_32':sum(v<=32 for v in values),'within_96':sum(v<=96 for v in values)}


def dictionary_bytes(vocab):
    assert vocab==sorted(set(vocab)) and 0<len(vocab)<=256
    return b'LTD1'+struct.pack('>I',len(vocab))+b''.join(struct.pack('>I',len(w.encode()))+w.encode() for w in vocab)


def measure(graph,active,folder,decoder_bytes,check=lambda:None):
    check();state=graph.initial(active);assert state['eligible'];vocab=sorted(active);ids={w:i for i,w in enumerate(vocab)}
    folder=Path(folder);folder.mkdir(parents=True);(folder/'packets').mkdir();c.write(folder/'dictionary.json',vocab)
    binary=dictionary_bytes(vocab);(folder/'dictionary.bin').write_bytes(binary);dh=hashlib.sha256(binary).digest()
    rows={};uses=Counter();owners={entry:set() for entry in range(len(vocab))}
    for pid,text in graph.texts.items():
        check();row=state['rows'][pid];sequence=[ids[w] for w in row['words']]
        assert ''.join(vocab[i] for i in sequence)==text and row['N']<=graph.caps[pid]
        packet=b'LTV1\x08'+dh+struct.pack('>I',len(sequence))+bytes(sequence)
        path=folder/'packets'/f'{pid}.bin';path.write_bytes(packet)
        rows[pid]={'source_sha256':hashlib.sha256(text.encode()).hexdigest(),'selections':row['N'],'actions':row['N']+1,
                   'characters':row['C'],'seed_cap':graph.caps[pid],'selection_delta_from_seed':row['N']-graph.caps[pid],
                   'packet_bytes':len(packet),'packet_sha256':c.sha(path),'one_program_package_bytes':len(binary)+len(packet),
                   'one_program_with_decoder':len(binary)+len(packet)+decoder_bytes}
        uses.update(sequence)
        for entry in set(sequence):owners[entry].add(pid)
    n=sum(r['selections'] for r in rows.values());chars=sum(r['characters'] for r in rows.values())
    package=len(binary)+sum(r['packet_bytes'] for r in rows.values())
    assert (chars,n,package+decoder_bytes)==(state['C'],state['N'],state['full_package_bytes'])
    result={'path_policy':'minimum_N_then_complete_sorted_subset_ID_sequence','per_problem':rows,
            'selections':distribution([r['selections'] for r in rows.values()]),'actions':distribution([r['actions'] for r in rows.values()]),
            'characters':chars,'character_fraction':chars/n,'exact_fraction':[chars,n],
            'score':[chars,n,package+decoder_bytes],'entries':len(vocab),'character_entries':sum(len(w)==1 for w in vocab),
            'dictionary_sha256':c.sha(folder/'dictionary.json'),'dictionary_bytes':len(binary),'package_bytes':package,
            'package_with_decoder_sources':package+decoder_bytes,'framing_bytes':41*len(rows),'payload_bits':8*n,'padding_bits':0,
            'seed_cap_regressions':0,'source_bytes':sum(len(t.encode()) for t in graph.texts.values())}
    check();return result
