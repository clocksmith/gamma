"""Matched target partitions and separate neural/final-coder cost accounting."""
from __future__ import annotations
import math
import struct
from pathlib import Path
from .fx2_training_capture import expected_rows, validate_rows

PARTITIONS = ('trained', 'other_neural', 'no_neural')


def target_mask(rows, starts, warmup=512, count=128):
    validate_rows(rows, len(rows)//2*410)
    markers = rows[1::2]
    selected = set()
    for start in starts:
        stop = start + warmup + count + 1
        if start < 0 or stop > len(markers) or markers[start] != 1:
            raise ValueError('training window does not begin at an actual reset')
        if any(markers[start+1:stop]):
            raise ValueError('training window crosses a reset')
        targets = set(range(start+warmup+1, stop))
        if targets & selected:
            raise ValueError('overlapping training target mask')
        selected |= targets
    if len(selected) != len(starts)*count:
        raise ValueError('mask cardinality differs')
    return selected


def analyze(prefix, expected_tokens, starts, raw_bytes, training_calls=None):
    prefix = str(prefix)
    tokens = Path(prefix+'.tokens').read_bytes()
    bits = Path(prefix+'.bits').read_bytes()
    neural = Path(prefix+'.neural').read_bytes()
    if tokens != expected_tokens or len(bits) != len(tokens)*12 or len(neural) != len(tokens)*8:
        raise ValueError('capture population or geometry differs')
    modeled = bytearray()
    for offset in range(0, len(bits), 24):
        value = 0
        for j in range(8):
            truth = bits[offset+3*j+2]
            if truth > 1:
                raise ValueError('invalid coded truth')
            value = (value << 1) | truth
        modeled.append(value)
    # The captured coder bytes independently determine tokens and native resets.
    wrapper = b'\x80\0\0\0\0\x07' + raw_bytes.to_bytes(4, 'big')
    if expected_rows(wrapper+modeled, raw_bytes) != tokens:
        raise ValueError('coder-to-token coordinate mismatch')
    selected = target_mask(tokens, starts)
    ncosts = {name: [] for name in PARTITIONS}
    fcosts = {name: [] for name in PARTITIONS}
    counts = dict.fromkeys(PARTITIONS, 0)
    trained_probabilities = {}
    for row, (index, token, marker, eligible, reserved, probability) in enumerate(struct.iter_unpack('<QBBBBf', neural)):
        expected_eligible = row > 0 and tokens[2*(row-1)+1] != 2
        if (index, token, marker, eligible, reserved) != (row, tokens[2*row], tokens[2*row+1], int(expected_eligible), 0):
            raise ValueError('neural target or next-token alignment differs')
        name = 'trained' if row in selected else 'other_neural' if eligible else 'no_neural'
        counts[name] += 1
        if eligible:
            if not math.isfinite(probability) or not 0 < probability <= 1:
                raise ValueError('invalid native FP32 truth probability')
            ncosts[name].append(-math.log2(probability))
            if name == 'trained':
                trained_probabilities[row] = probability
        elif name == 'trained' or probability != 0:
            raise ValueError('training mask includes an unavailable neural prediction')
        for j in range(8):
            offset = row*24 + 3*j
            p = int.from_bytes(bits[offset:offset+2], 'little')
            truth = bits[offset+2]
            if not 0 < p < 65536:
                raise ValueError('invalid final integer probability')
            fcosts[name].append(-math.log2((p if truth else 65536-p)/65536))
    cells = {name: {'targets': counts[name], 'coded_bits': 8*counts[name],
                   'neural_bits': math.fsum(ncosts[name]) if name != 'no_neural' else None,
                   'final_bits': math.fsum(fcosts[name])} for name in PARTITIONS}
    total = {'targets': len(tokens)//2, 'coded_bits': len(bits)//3,
             'neural_targets': len(ncosts['trained'])+len(ncosts['other_neural']),
             'neural_bits': math.fsum(cells[n]['neural_bits'] for n in PARTITIONS if n != 'no_neural'),
             'final_bits': math.fsum(cells[n]['final_bits'] for n in PARTITIONS)}
    window_check = None
    if training_calls is not None:
        matches = 0
        old_costs = []
        max_difference = 0
        for wi, start in enumerate(starts):
            previous = (Path(training_calls)/f'w{wi}.f32').read_bytes()
            if len(previous) != 641*410*4:
                raise ValueError('retained training evaluation geometry differs')
            for target in range(start+513, start+641):
                old = struct.unpack_from('<f', previous, ((target-start-1)*410+205+tokens[2*target])*4)[0]
                current = trained_probabilities[target]
                matches += struct.pack('<f', current) == struct.pack('<f', old)
                max_difference = max(max_difference, abs(current-old))
                old_costs.append(-math.log2(old))
        window_check = {'targets': len(selected), 'bitwise_equal_truth_probabilities': matches,
                        'maximum_absolute_truth_probability_difference': max_difference,
                        'retained_window_neural_bits': math.fsum(old_costs),
                        'complete_minus_window_neural_bits': cells['trained']['neural_bits']-math.fsum(old_costs)}
    return {'partitions': cells, 'total': total, 'training_window_check': window_check}


def differences(measurements, archives):
    baseline = measurements['P']
    out = {}
    for arm, value in measurements.items():
        cells = {}
        for name in (*PARTITIONS, 'total'):
            a = value['total'] if name == 'total' else value['partitions'][name]
            p = baseline['total'] if name == 'total' else baseline['partitions'][name]
            if a['targets'] != p['targets'] or a['coded_bits'] != p['coded_bits']:
                raise ValueError('unmatched attribution populations')
            cells[name] = {'delta_neural_bits': None if a['neural_bits'] is None else a['neural_bits']-p['neural_bits'],
                           'delta_final_bits': a['final_bits']-p['final_bits']}
        delta_bytes = archives[arm]-archives['P']
        out[arm] = {'partitions': cells, 'archive_delta_bytes': delta_bytes,
                    'coding_residual_bits': 8*delta_bytes-cells['total']['delta_final_bits']}
    return out
