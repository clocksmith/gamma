#!/usr/bin/env python3
"""Conditional cache coding from authenticated, truth-free parent observations."""
import hashlib
import json
from pathlib import Path
import struct
import sys

from lib.fx2_causal_residual_v1 import feature_rows
from lib.fx2_hidden_cache_v1 import Model
from tools.causal_field_parent_coder_v1 import Encoder, Decoder
from tools.fx2_final_counts_replay_v1 import project as parent_project
from tools.wrt_exact import parse_store_bytes, read_dictionary_words


def digest(data): return hashlib.sha256(data).hexdigest()


def write(path, data):
    with path.open('xb') as f: f.write(data)


def report(path, value):
    write(path, (json.dumps(value, sort_keys=True, indent=2)+'\n').encode())


def project(root, out):
    native = root/'results/fx2_residual_features250k_v3/work/native'
    stored = (root/'results/fx2_weight_native_transfer250k_q0_v1/work/native/opening.stored').read_bytes()
    raw = (native/'population.raw').read_bytes(); body = stored[10:]
    words = read_dictionary_words(native/'dictionary/english.dic')
    decoded = parse_store_bytes(stored, words)
    if decoded.decoded != raw or decoded.stream[5:] != body or len(raw) != 250000 or len(body) != 151210:
        raise ValueError('population or exact inverse differs')
    features = (native/'encode.features').read_bytes()
    coder = (native/'encode.coder').read_bytes(); archive = (native/'encode.arc').read_bytes()
    q16 = parent_project(coder, body, archive)
    signatures = bytearray()
    for i, (packed, c, y) in enumerate(feature_rows(features, body, coder)):
        if i % 8 == 0:
            valid = int(bool(features[12*i+10] & 8))
            signatures.extend(struct.pack('<QB', packed, valid))
    write(out/'signatures.bin', signatures); write(out/'parent.q16', q16)
    write(out/'population.modeled', body); write(out/'prefix.bin', archive[:46])
    report(out/'projection.json', dict(exact_parent_replay=True, exact_wrt_inverse=True,
        raw_bytes=len(raw), raw_sha256=digest(raw), modeled_bytes=len(body), modeled_sha256=digest(body),
        parent_archive_bytes=len(archive), parent_archive_sha256=digest(archive),
        parent_count_bytes=len(q16), parent_count_sha256=digest(q16),
        signature_bytes=len(signatures), signature_sha256=digest(signatures),
        signatures_contain_truth=False, objective_credit_bytes=0))


def replay(root, out, operation, arm, library):
    metadata = json.loads((out/'projection.json').read_text())
    counts = (out/'parent.q16').read_bytes(); signatures = (out/'signatures.bin').read_bytes()
    prefix = (out/'prefix.bin').read_bytes(); n = metadata['modeled_bytes']; events = n*8
    if len(counts) != 16*n or len(signatures) != 9*n or len(prefix) != 46:
        raise ValueError('conditional input framing differs')
    if digest(counts) != metadata['parent_count_sha256'] or digest(signatures) != metadata['signature_sha256']:
        raise ValueError('conditional input digest differs')
    source = (out/(arm+'-encode.arc')).read_bytes() if operation == 'decode' else (
        out/(arm+'-decode.modeled' if operation == 'repeat' else 'population.modeled')).read_bytes()
    if operation == 'decode':
        if source[:46] != prefix: raise ValueError('archive prefix differs')
        decoder = Decoder(source[46:], max_bits=events, max_payload_bytes=2*n,
                          expected_payload_bytes=len(source)-46, payload_sha256=digest(source[46:]))
    else:
        if len(source) != n or digest(source) != metadata['modeled_sha256']:
            raise ValueError('modeled input differs')
        decoder = None
    encoder = Encoder(max_bits=events, max_payload_bytes=2*n)
    restored = bytearray(n); probabilities = hashlib.sha256(); states = hashlib.sha256()
    trajectory = hashlib.sha256(); checkpoints = []; changed = 0
    with Model(library, arm) as model:
        states.update(model.state())
        for i, (parent,) in enumerate(struct.iter_unpack('<H', counts)):
            if i % 8 == 0: packed, valid = struct.unpack_from('<QB', signatures, 9*(i//8))
            q = model.predict(parent, packed, valid); changed += q != parent
            probabilities.update(struct.pack('<H', q))
            y = decoder.decode(q) if decoder else source[i//8] >> (7-i%8) & 1
            encoder.encode(y, q); model.observe(y)
            if decoder and (decoder.low, decoder.high) != (encoder.low, encoder.high):
                raise ValueError('independent arithmetic interval differs')
            restored[i//8] = (restored[i//8] << 1) | y
            trajectory.update(struct.pack('<HII', q, encoder.low, encoder.high))
            if (i+1) % 2048 == 0 or i+1 == events:
                state = model.state(); states.update(struct.pack('<Q', i+1)); states.update(state)
                checkpoints.append([i+1, digest(state), probabilities.hexdigest()])
        state = model.state()
        counters = struct.unpack_from('<6Q', state, 38054)
        used = struct.unpack_from('<I', state, 12)[0]
    if digest(restored) != metadata['modeled_sha256']: raise ValueError('modeled inverse differs')
    archive = prefix + encoder.finish()
    if decoder and archive != source: raise ValueError('canonical arithmetic termination differs')
    dictionary = root/'results/fx2_residual_features250k_v3/work/native/dictionary/english.dic'
    raw = parse_store_bytes(b'\x07'+metadata['raw_bytes'].to_bytes(4,'big')+restored,
                            read_dictionary_words(dictionary)).decoded
    if digest(raw) != metadata['raw_sha256'] or len(raw) != metadata['raw_bytes']:
        raise ValueError('raw inverse differs')
    if operation == 'decode':
        write(out/(arm+'-decode.raw'), raw); write(out/(arm+'-decode.modeled'), restored)
    else: write(out/(arm+'-'+operation+'.arc'), archive)
    result = dict(arm=arm,operation=operation,archive_bytes=len(archive),archive_sha256=digest(archive),
        raw_bytes=len(raw),raw_sha256=digest(raw),modeled_sha256=digest(restored),events=events,
        changed_probability_events=changed,probability_sha256=probabilities.hexdigest(),
        controller_state_sha256=states.hexdigest(),final_state_sha256=digest(state),
        coder_trajectory_sha256=trajectory.hexdigest(),state_boundaries=len(checkpoints),checkpoints=checkpoints,
        cache_used=used,queries=counters[0],queries_with_neighbors=counters[1],neighbors_selected=counters[2],
        active_expert_events=counters[3],hypothetical_changed_events=counters[4],insertions=counters[5],
        exact_inverse=True,standalone_decoder=False,complete_package_bytes=None,full_corpus_score_bytes=None,
        parent_count_dependency_bytes=len(counts),signature_dependency_bytes=len(signatures),
        dictionary_dependency_bytes=dictionary.stat().st_size,objective_credit_bytes=0)
    report(out/(arm+'-'+operation+'.json'), result)
    print(json.dumps({k:result[k] for k in ('arm','operation','archive_bytes','changed_probability_events','queries_with_neighbors')}))


def main():
    root, out = map(Path, sys.argv[1:3]); operation = sys.argv[3]
    if operation == 'project': project(root, out)
    elif operation in ('encode', 'decode', 'repeat') and len(sys.argv) == 6 and sys.argv[4] in ('K', 'D', 'S'):
        replay(root, out, operation, sys.argv[4], Path(sys.argv[5]))
    else: raise ValueError('invalid invocation')


if __name__ == '__main__': main()
