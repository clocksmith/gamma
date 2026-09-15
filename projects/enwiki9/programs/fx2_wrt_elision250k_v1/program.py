"""Conditional finite-coder test of vocabulary and source-proved WRT elision."""
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

from lib.fx2_wrt_elision_v1 import Grammar
from tools.causal_field_parent_coder_v1 import Encoder, Decoder
from tools.fx2_final_counts_replay_v1 import project as parent_project, framing
from tools.wrt_exact import parse_store_bytes, read_dictionary_words


def digest(data): return hashlib.sha256(data).hexdigest()


def write(path, data):
    with path.open('xb') as f: f.write(data)


def report(path, data): write(path, (json.dumps(data, indent=2, sort_keys=True)+'\n').encode())


def project(root, out):
    native = root/'results/fx2_residual_features250k_v3/work/native'
    stored = (root/'results/fx2_weight_native_transfer250k_q0_v1/work/native/opening.stored').read_bytes()
    raw = (native/'population.raw').read_bytes(); body = stored[10:]
    words = read_dictionary_words(native/'dictionary/english.dic')
    parsed = parse_store_bytes(stored, words)
    if parsed.decoded != raw or parsed.stream[5:] != body or len(raw) != 250000 or len(body) != 151210:
        raise ValueError('population or raw inverse differs')
    archive = (native/'encode.arc').read_bytes()
    q16 = parent_project((native/'encode.coder').read_bytes(), body, archive)
    write(out/'parent.q16', q16); write(out/'population.modeled', body); write(out/'prefix.bin', archive[:46])
    report(out/'projection.json', dict(exact_parent_replay=True, exact_wrt_inverse=True,
        raw_bytes=len(raw), raw_sha256=digest(raw), modeled_bytes=len(body), modeled_sha256=digest(body),
        parent_archive_bytes=len(archive), parent_archive_sha256=digest(archive),
        parent_count_bytes=len(q16), parent_count_sha256=digest(q16), word_count=len(words),
        counts_contain_no_truth_field=True, objective_credit_bytes=0))


def replay(root, out, operation, arm):
    metadata = json.loads((out/'projection.json').read_text())
    counts = (out/'parent.q16').read_bytes(); prefix = (out/'prefix.bin').read_bytes()
    n = metadata['modeled_bytes']; events = 8*n
    if len(counts) != 2*events or digest(counts) != metadata['parent_count_sha256']:
        raise ValueError('conditional count dependency differs')
    raw_bytes, allowed = framing(prefix, n)
    dictionary = root/'results/fx2_residual_features250k_v3/work/native/dictionary/english.dic'
    words = read_dictionary_words(dictionary)
    if len(words) != metadata['word_count']: raise ValueError('dictionary count differs')
    model = Grammar(len(words), allowed)
    header = b'' if arm == 'K' else bytes([1, {'V': 0, 'D': 1}[arm]])
    source = (out/(arm+'-encode.arc')).read_bytes() if operation == 'decode' else (
        out/(arm+'-decode.modeled' if operation == 'repeat' else 'population.modeled')).read_bytes()
    start = len(header) + 46
    if operation == 'decode':
        if source[:start] != header+prefix: raise ValueError('archive framing differs')
        decoder = Decoder(source[start:], max_bits=events, max_payload_bytes=2*n,
                          expected_payload_bytes=len(source)-start, payload_sha256=digest(source[start:]))
    else:
        if len(source) != n or digest(source) != metadata['modeled_sha256']:
            raise ValueError('modeling input differs')
        decoder = None
    encoder = Encoder(max_bits=events, max_payload_bytes=2*n)
    restored = bytearray(n); states = hashlib.sha256(); actions = hashlib.sha256()
    states.update(model.state()); checkpoints = []; elided = 0; forced_opportunities = 0
    removed_ideal_bits = 0.0; partitions = [dict(elided=0, ideal_bits=0.0) for _ in range(3)]
    for i, (parent,) in enumerate(struct.iter_unpack('<H', counts)):
        if not 1 <= parent <= 65535: raise ValueError('invalid parent count')
        forced = model.forced(grammar=arm != 'V')
        forced_opportunities += forced is not None
        skip = arm != 'K' and forced is not None
        if decoder:
            y = forced if skip else decoder.decode(parent)
        else: y = source[i//8] >> (7-i%8) & 1
        if forced is not None and forced != y: raise ValueError('forced outcome contradicted by source')
        if skip:
            elided += 1
            bits = -math.log2((parent if y else 65536-parent)/65536)
            removed_ideal_bits += bits
            part = min(2, i*3//events); partitions[part]['elided'] += 1; partitions[part]['ideal_bits'] += bits
        else: encoder.encode(y, parent)
        if decoder and (encoder.low, encoder.high) != (decoder.low, decoder.high):
            raise ValueError('independent arithmetic interval differs')
        actions.update(struct.pack('<HB', parent, 2 if not skip else y))
        model.observe(y); restored[i//8] = (restored[i//8] << 1) | y
        if i%8 == 7: states.update(model.state())
        if (i+1)%2048 == 0 or i+1 == events:
            checkpoints.append([i+1, digest(model.state()), actions.hexdigest()])
    model.finish()
    if digest(restored) != metadata['modeled_sha256']: raise ValueError('modeled inverse differs')
    archive = header+prefix+encoder.finish()
    if decoder and archive != source: raise ValueError('canonical termination differs')
    raw = parse_store_bytes(b'\x07'+raw_bytes.to_bytes(4,'big')+restored, words).decoded
    if len(raw) != metadata['raw_bytes'] or digest(raw) != metadata['raw_sha256']:
        raise ValueError('independent raw inverse differs')
    if decoder:
        write(out/(arm+'-decode.raw'), raw); write(out/(arm+'-decode.modeled'), restored)
    else: write(out/(arm+'-'+operation+'.arc'), archive)
    result = dict(arm=arm, operation=operation, archive_bytes=len(archive), archive_sha256=digest(archive),
        raw_bytes=len(raw), raw_sha256=digest(raw), modeled_sha256=digest(restored), events=events,
        elided_events=elided, forced_opportunities=forced_opportunities, action_sha256=actions.hexdigest(),
        grammar_state_sha256=states.hexdigest(), final_state_sha256=digest(model.state()),
        state_boundaries=n+1, checkpoints=checkpoints, removed_ideal_bits_diagnostic=removed_ideal_bits,
        thirds=partitions, archive_header_bytes=len(header), exact_inverse=True,
        standalone_decoder=False, parent_count_dependency_bytes=len(counts),
        dictionary_dependency_bytes=dictionary.stat().st_size, complete_package_bytes=None,
        full_corpus_score_bytes=None, objective_credit_bytes=0)
    report(out/(arm+'-'+operation+'.json'), result)
    print(json.dumps({k:result[k] for k in ('arm','operation','archive_bytes','elided_events')}))


def main():
    root, out = map(Path, sys.argv[1:3]); operation = sys.argv[3]
    if operation == 'project' and len(sys.argv) == 4: project(root, out)
    elif operation in ('encode','decode','repeat') and len(sys.argv) == 5 and sys.argv[4] in ('K','V','D'):
        replay(root, out, operation, sys.argv[4])
    else: raise ValueError('unsupported invocation')


if __name__ == '__main__': main()
