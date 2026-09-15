#!/usr/bin/env python3
"""Verify finite arithmetic for the unchanged, previously frozen scalar grid."""
import hashlib
import json
from pathlib import Path
import struct
import sys

from lib.fx2_causal_residual_v1 import AMPLITUDES, Controller, corrected, headroom
from tools.causal_field_parent_coder_v1 import Encoder, Decoder
from tools.fx2_final_counts_replay_v1 import project
from tools.wrt_exact import parse_store_bytes, read_dictionary_words


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    root, out = map(Path, sys.argv[1:])
    out.mkdir()
    native = root / 'results/fx2_residual_features250k_v3/work/native'
    stored = (root / 'results/fx2_weight_native_transfer250k_q0_v1/work/native/opening.stored').read_bytes()
    raw = (native / 'population.raw').read_bytes()
    words = read_dictionary_words(native / 'dictionary/english.dic')
    parsed = parse_store_bytes(stored, words)
    body = stored[10:]
    if parsed.decoded != raw or parsed.stream[5:] != body or len(raw) != 250000 or len(body) != 151210:
        raise ValueError('population or WRT inverse differs')
    features = (native / 'encode.features').read_bytes()
    coder = (native / 'encode.coder').read_bytes()
    parent = (native / 'encode.arc').read_bytes()
    q16 = project(coder, body, parent)
    report, vectors = headroom(features, body, coder)
    report.update(parent_archive_bytes=len(parent), exact_parent_replay=True, exact_wrt_inverse=True,
                  source_scope='Exposed raw[0,250000), cold parent; no confirmation.',
                  standalone_decoder=False, conditional_feature_bytes=len(features),
                  conditional_parent_count_bytes=len(q16), dictionary_bytes=(native / 'dictionary/english.dic').stat().st_size,
                  complete_package_bytes=None, full_corpus_score_bytes=None, objective_credit_bytes=0,
                  shared_code_cost_unknown=True, native_integration_authorized=False)
    with (out / 'headroom.json').open('x') as f:
        json.dump(report, f, sort_keys=True, indent=2); f.write('\n')
    # Verify the finite-coder cost excluded by the prior ideal bound.
    report['finite_coding_verification'] = True
    rows = []
    counts = list(struct.iter_unpack('<H', q16))
    for j, label in enumerate(('D', 'S')):
        numerators, norms = vectors[j]
        for index, k in enumerate(AMPLITUDES):
            enc = Encoder(max_bits=len(body) * 8, max_payload_bytes=2 * len(body))
            probabilities = hashlib.sha256()
            changed = 0
            for i, ((c,), a, m) in enumerate(zip(counts, numerators, norms)):
                q = corrected(c, k, a, m)
                changed += q != c
                probabilities.update(struct.pack('<H', q))
                enc.encode((body[i // 8] >> (7 - i % 8)) & 1, q)
            archive = bytes((1, index)) + parent[:46] + enc.finish()
            if not k and archive[2:] != parent:
                raise ValueError('zero correction bookkeeping differs from parent')
            (out / (label + str(index) + '.arc')).write_bytes(archive)
            rows.append(dict(arm=label, index=index, coefficient=k, archive_bytes=len(archive),
                             archive_sha256=digest(archive), probability_sha256=probabilities.hexdigest(),
                             changed_events=changed))
    selected = []
    for j, label in enumerate(('D', 'S')):
        best = min((r for r in rows if r['arm'] == label), key=lambda r: (r['archive_bytes'], r['index']))
        archive = (out / (label + str(best['index']) + '.arc')).read_bytes()
        if archive[:2] != bytes((1, best['index'])) or archive[2:48] != parent[:46]:
            raise ValueError('header differs')
        dec = Decoder(archive[48:], max_bits=len(body) * 8, max_payload_bytes=2 * len(body),
                      expected_payload_bytes=len(archive) - 48, payload_sha256=digest(archive[48:]))
        enc = Encoder(max_bits=len(body) * 8, max_payload_bytes=2 * len(body))
        controller = Controller(j == 1)
        restored = bytearray(len(body))
        probabilities = hashlib.sha256()
        state = hashlib.sha256()
        # Deliberately ignore the recorded truth field here. The only truth
        # used by the controller is decoded from the arithmetic archive.
        for i, (packed, c, flags, _unused_truth) in enumerate(struct.iter_unpack('<QHBB', features)):
            a, m = controller.predict(c, packed)
            q = corrected(c, best['coefficient'], a, m)
            probabilities.update(struct.pack('<H', q))
            y = dec.decode(q)
            enc.encode(y, q)
            if (enc.low, enc.high) != (dec.low, dec.high):
                raise ValueError('independent decoder interval differs')
            restored[i // 8] = (restored[i // 8] << 1) | y
            controller.observe(y)
            if i % 8 == 7:
                state.update(controller.state())
        if restored != body or archive[48:] != enc.finish():
            raise ValueError('selected arithmetic inverse or canonical termination differs')
        decoded = parse_store_bytes(stored[:10] + restored, words).decoded
        if decoded != raw or probabilities.hexdigest() != best['probability_sha256']:
            raise ValueError('selected raw inverse or probability witness differs')
        if state.hexdigest() != report['arms'][j]['state_sha256']:
            raise ValueError('complete controller state witness differs')
        (out / (label + '.raw')).write_bytes(decoded)
        selected.append(dict(**best, exact_inverse=True, decoded_sha256=digest(decoded),
                             decoder_probability_identity=True, controller_state_identity=True))
    gain = len(parent) - selected[0]['archive_bytes']
    separation = selected[1]['archive_bytes'] - selected[0]['archive_bytes']
    report.update(finite_replay=True, candidates=rows, selected=selected, gain_parent_bytes=gain,
                  gain_control_bytes=separation, zero_correction_parent_identity=True,
                  conditional_candidate_pays=gain > 0 and separation > 0,
                  verdict='Conditional causal correction earns native testing, subject to complete source cost.'
                  if gain > 0 and separation > 0 else 'Frozen local correction grid fails conditional archive/control economics.')
    with (out / 'report.json').open('x') as f:
        json.dump(report, f, indent=2, sort_keys=True); f.write('\n')
    print(json.dumps({k: report.get(k) for k in ('verdict', 'finite_replay', 'gain_parent_bytes', 'gain_control_bytes')}))


if __name__ == '__main__':
    main()
