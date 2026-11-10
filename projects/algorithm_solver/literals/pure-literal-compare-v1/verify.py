"""Independent source-free-report verification of private literal packages.

Decode by direct bit slicing, not the producer's decoder, and use a forward
shortest-path oracle rather than the producer's backward segmentation.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics
import struct


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def decode(raw, packet, expected_width=None):
    if raw[:4] != b'LTD1' or len(raw) < 8:
        raise ValueError('Dictionary header')
    k = struct.unpack_from('>I', raw, 4)[0]
    offset, entries = 8, []
    for _ in range(k):
        n = struct.unpack_from('>I', raw, offset)[0]
        offset += 4
        text = raw[offset:offset+n].decode()
        if not n or len(text.encode()) != n:
            raise ValueError('Dictionary entry')
        entries.append(text)
        offset += n
    if offset != len(raw) or len(set(entries)) != k:
        raise ValueError('Dictionary framing/uniqueness')
    if packet[:4] != b'LTV1' or len(packet) < 41 or packet[5:37].hex() != sha(raw):
        raise ValueError('Packet identity')
    width = packet[4]
    if expected_width is not None and width != expected_width:
        raise ValueError('Packet width differs from reported width')
    count = struct.unpack_from('>I', packet, 37)[0]
    if width not in [6, 7, 8] or k > 1 << width or len(packet) != 41 + math.ceil(count * width / 8):
        raise ValueError('Packet length/capacity')
    bits = ''.join(format(c, '08b') for c in packet[41:])
    if any(c != '0' for c in bits[count * width:]):
        raise ValueError('Padding')
    ids = [int(bits[i*width:(i+1)*width], 2) for i in range(count)]
    if any(i >= len(entries) for i in ids):
        raise ValueError('Unused opcode')
    return entries, ids, ''.join(entries[i] for i in ids)


def minimum(text, entries):
    costs = [0] + [float('inf')] * len(text)
    for i in range(len(text)):
        if not math.isfinite(costs[i]):
            continue
        for literal in entries:
            if text.startswith(literal, i):
                end = i + len(literal)
                costs[end] = min(costs[end], costs[i] + 1)
    return costs[-1]


def metrics(values):
    if not values:
        return None
    s = sorted(values)
    return {'n': len(s), 'total': sum(s), 'mean': statistics.mean(s), 'p50': statistics.median(s),
            'p95': s[math.ceil(.95 * len(s)) - 1], 'worst': s[-1]}


def verify(private):
    report = json.loads((private / 'results.json').read_bytes())
    if report.get('schema') != 'gamma.pure-literal-development.v1' or set(report.get('languages', {})) != {'javascript', 'python'}:
        raise ValueError('Language population or schema changed')
    contract = json.loads((private / 'contract.json').read_bytes())
    if contract != report.get('contract'):
        raise ValueError('Contract changed')
    split_path = Path(__file__).resolve().parent.parent / 'cost-decomposition-v1/contract.json'
    split_raw = split_path.read_bytes()
    if sha(split_raw) != 'a2c501792e4ef369a1f2630fd4ffd3b6623c1146ca3d7aac7115b469efe8cd61' or contract['partition_sha256'] != sha(split_raw):
        raise ValueError('Original partition differs')
    split_ids = json.loads(split_raw)['partition']
    if contract['fit_ids'] != split_ids['dev_fit'] or contract['validation_ids'] != split_ids['dev_val']:
        raise ValueError('Contract population differs')
    checks, uncovered, source_hash_matches = 0, 0, 0
    for language, data in report['languages'].items():
        folder = private / language
        seal = folder / 'sealed-tables.json'
        if sha(seal.read_bytes()) != data['seal_sha256']:
            raise ValueError('Seal changed')
        tables = json.loads(seal.read_bytes())
        if set(tables) != {'6', '7', '8'}:
            raise ValueError('Frozen width population changed')
        for split, population in [('fit', 300), ('validation', 100)]:
            members = {str(m['id']): m for m in data[split + '_membership'] if m['status'] == 'available'}
            if len(data[split + '_membership']) != population or len({m['id'] for m in data[split + '_membership']}) != population:
                raise ValueError('Population changed')
            if {m['id'] for m in data[split + '_membership']} != set(contract[split + '_ids']):
                raise ValueError('Membership differs from original frozen partition')
            if set(data[split]) != {'6', '7', '8'}:
                raise ValueError('Report width population changed')
            for width, record in data[split].items():
                target = folder / (split + '-' + width)
                raw = (target / 'dictionary.ltd').read_bytes()
                entries = tables[width]
                if not entries or len(entries) != len(set(entries)) or any(not isinstance(x, str) or not x for x in entries) or len(entries) > 1 << int(width):
                    raise ValueError('Illegal literal table')
                expected_raw = b'LTD1' + struct.pack('>I', len(entries)) + b''.join(
                    struct.pack('>I', len(x.encode())) + x.encode() for x in entries)
                if raw != expected_raw:
                    raise ValueError('Table differs from frozen bytes')
                counts, packets, payload, singleton, used = [], 0, 0, 0, set()
                if len(record['rows']) != len(members) or {str(r['id']) for r in record['rows']} != set(members):
                    raise ValueError('Membership changed')
                expected_packets = set()
                for row in record['rows']:
                    pid = str(row['id'])
                    source_raw = (folder / split / (pid + '.source')).read_bytes()
                    if sha(source_raw) != row['source_sha256'] or sha(source_raw) != members[pid]['source_sha256']:
                        raise ValueError('Receipt-bound source hash differs')
                    source_hash_matches += 1
                    optimum = minimum(source_raw.decode(), entries)
                    if row['status'] == 'uncovered':
                        if math.isfinite(optimum):
                            raise ValueError('False uncovered source')
                        uncovered += 1
                        continue
                    if row['status'] != 'represented':
                        raise ValueError('Unknown coverage status')
                    packet = (target / (pid + '.ltv')).read_bytes()
                    expected_packets.add(pid + '.ltv')
                    table, ids, source = decode(raw, packet, int(width))
                    n, w = len(ids), int(width)
                    single = sum(len(table[i]) == 1 for i in ids) * w
                    if source.encode() != source_raw or n != optimum:
                        raise ValueError('Reconstruction or shortest cost differs')
                    expect = {'selections': n, 'payload_bits': n*w, 'singleton_bits': single,
                        'packet_bytes': len(packet), 'padding_bits': (-n*w) % 8, 'packet_sha256': sha(packet)}
                    if any(row[k] != v for k, v in expect.items()):
                        raise ValueError('Per-packet accounting differs')
                    counts.append(n)
                    packets += len(packet)
                    payload += n*w
                    singleton += single
                    used.update(ids)
                    checks += 1
                if {p.name for p in target.glob('*.ltv')} != expected_packets:
                    raise ValueError('Unexpected or missing packets')
                expect = {'population': population, 'available': len(members), 'represented': len(counts),
                    'uncovered': len(members) - len(counts), 'unavailable': population - len(members),
                    'dictionary_entries': len(entries), 'used_entries': len(used), 'dictionary_bytes': len(raw),
                    'dictionary_sha256': sha(raw), 'selections': metrics(counts), 'payload_bits': payload,
                    'singleton_bits': singleton, 'singleton_fraction': singleton/payload if payload else None,
                    'packet_bytes': packets, 'framing_bytes_per_packet': 41,
                    'dictionary_plus_packets_bytes': len(raw) + packets}
                if expect != record['summary']:
                    raise ValueError('Summary differs')
    return {'schema': 'gamma.pure-literal-independent-verification.v1', 'results_sha256': sha((private / 'results.json').read_bytes()),
            'packets_reconstructed_and_minimum_cost_verified': checks, 'uncovered_sources_verified': uncovered,
            'receipt_source_hash_matches': source_hash_matches, 'source_execution': False}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--private', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    result = verify(args.private)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps(result, sort_keys=True))
