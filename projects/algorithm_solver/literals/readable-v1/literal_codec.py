"""Fixed-dictionary byte parsing only. Never imports or executes candidate source."""
from pathlib import Path
import collections, hashlib, json, math, statistics, time

D = Path(__file__).resolve().parent
sha = lambda b: hashlib.sha256(b).hexdigest()


def decode_dictionary(raw):
    assert len(raw) >= 8 and raw[:4] == b'LTD1', 'dictionary header'
    count = int.from_bytes(raw[4:8], 'big')
    assert 0 < count <= 256, 'dictionary count'
    pos, literals = 8, []
    for _ in range(count):
        assert pos + 4 <= len(raw), 'dictionary length truncated'
        length = int.from_bytes(raw[pos:pos+4], 'big')
        pos += 4
        assert length > 0 and pos + length <= len(raw), 'dictionary literal truncated/empty'
        value = raw[pos:pos+length]
        value.decode('utf-8')
        literals.append(value)
        pos += length
    assert pos == len(raw), 'dictionary trailing bytes'
    assert len(set(literals)) == len(literals), 'duplicate literal'
    return literals


def parse(raw, literals):
    """Backward unit-cost DAG DP, lower dictionary ID breaks equal costs."""
    n = len(raw)
    costs = [n + 1] * (n + 1)
    choices = [None] * (n + 1)
    costs[n] = 0
    byfirst = collections.defaultdict(list)
    for i, value in enumerate(literals):
        assert value
        byfirst[value[0]].append((i, value))
    for pos in range(n - 1, -1, -1):
        for i, value in byfirst[raw[pos]]:
            end = pos + len(value)
            if end <= n and raw.startswith(value, pos) and costs[end] + 1 < costs[pos]:
                costs[pos] = costs[end] + 1
                choices[pos] = i
    if choices[0] is None:
        alphabet = set(b''.join(literals))
        return None, [{'offset': i, 'byte': b} for i, b in enumerate(raw) if b not in alphabet]
    ids, pos = [], 0
    while pos < n:
        i = choices[pos]
        assert i is not None
        ids.append(i)
        pos += len(literals[i])
    # Independent forward recurrence, including unreachable offsets.
    forward = [n + 1] * (n + 1)
    forward[0] = 0
    for pos in range(n):
        if forward[pos] == n + 1:
            continue
        for _, value in byfirst[raw[pos]]:
            if raw.startswith(value, pos):
                end = pos + len(value)
                forward[end] = min(forward[end], forward[pos] + 1)
    assert forward[n] == len(ids) == costs[0]
    assert b''.join(literals[i] for i in ids) == raw
    return ids, []


def packet(ids, width, dictionary):
    bits = ''.join(format(i, f'0{width}b') for i in ids)
    bits += '0' * (-len(bits) % 8)
    payload = bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))
    return b'LTV1' + bytes([width]) + hashlib.sha256(dictionary).digest() + len(ids).to_bytes(4, 'big') + payload


def verify_packet(raw, dictionary, literals, source):
    binary_literals = decode_dictionary(dictionary)
    assert literals == binary_literals, 'JSON/binary dictionary mismatch'
    assert len(raw) >= 41 and raw[:4] == b'LTV1', 'packet header'
    assert raw[5:37] == hashlib.sha256(dictionary).digest(), 'dictionary hash mismatch'
    width, count = raw[4], int.from_bytes(raw[37:41], 'big')
    assert 1 <= width <= 8 and len(binary_literals) <= 2**width, 'invalid width'
    bits = ''.join(format(b, '08b') for b in raw[41:])
    assert len(raw) == 41 + math.ceil(count * width / 8)
    assert '1' not in bits[count * width:]
    ids = [int(bits[i*width:(i+1)*width], 2) for i in range(count)]
    assert all(i < len(binary_literals) for i in ids), 'unused ID'
    assert b''.join(binary_literals[i] for i in ids) == source, 'decoded source mismatch'


def measure(sources, output_name):
    started = time.monotonic()
    c = json.loads((D/'contract.json').read_text())
    rows, profiles = [], []
    out = D/output_name
    out.mkdir(exist_ok=False)
    for p in c['profiles']:
        dictionary = (D/p['files']['dictionary.bin']['snapshot']).read_bytes()
        assert sha(dictionary) == p['files']['dictionary.bin']['sha256']
        json_bytes = (D/p['files']['dictionary.json']['snapshot']).read_bytes()
        assert sha(json_bytes) == p['files']['dictionary.json']['sha256']
        strings = json.loads(json_bytes)
        literals = decode_dictionary(dictionary)
        assert literals == [s.encode() for s in strings], 'ordered dictionary parity'
        uses = collections.defaultdict(set)
        current = []
        for s in sources:
            if s['entry'].split(':')[1] != p['language']:
                continue
            raw = (D/s['snapshot']).read_bytes()
            assert sha(raw) == s['sha256']
            ids, absent = parse(raw, literals)
            row = {'entry': s['entry'], 'variant': s.get('variant', 'admitted-original'), 'profile': p['id'], 'source_sha256': sha(raw), 'source_bytes': len(raw), 'represented': ids is not None, 'absent_bytes': absent}
            if ids is not None:
                b = packet(ids, p['width'], dictionary)
                verify_packet(b, dictionary, literals, raw)
                name = s['entry'].replace(':','-') + '-' + row['variant'] + '-' + p['id']
                (out/(name+'.ltv')).write_bytes(b)
                (out/(name+'.sequence.json')).write_text(json.dumps(ids)+'\n')
                chars = sum(len(strings[i]) == 1 for i in ids)
                nonchars = len(ids) - chars
                row.update(selections=len(ids), selection_bits=len(ids)*p['width'], single_character_selections=chars, single_character_fraction=chars/len(ids), noncharacter_selections=nonchars, unique_entries=len(set(ids)), packet_bytes=len(b), framing_bytes=41, padding_bits=8*(len(b)-41)-len(ids)*p['width'], packet_sha256=sha(b), packet_file=str((out/(name+'.ltv')).relative_to(D)), whole_solution_entries=sum(value==raw for value in literals))
                for i in set(ids):
                    uses[i].add(s['entry'])
            rows.append(row)
            current.append(row)
        covered = [r for r in current if r['represented']]
        counts = [r['selections'] for r in covered]
        profile = {'profile':p['id'], 'entries':len(literals), 'width':p['width'], 'denominator':len(current), 'covered':len(covered), 'dictionary_utf8_bytes':sum(map(len,literals)), 'dictionary_framing_bytes':8+4*len(literals), 'dictionary_bytes':len(dictionary), 'dictionary_sha256':sha(dictionary), 'used_entries':len(uses), 'unused_entries':len(literals)-len(uses), 'entries_reused_across_problems':sum(len(v)>1 for v in uses.values()), 'noncharacter_entries_reused_across_problems':sum(len(v)>1 and len(strings[i])>1 for i,v in uses.items()), 'reused_noncharacter_strings':[{'id':i,'literal':strings[i],'problem_count':len(v)} for i,v in uses.items() if len(v)>1 and len(strings[i])>1]}
        if covered:
            profile.update(selections=sum(counts), median=statistics.median(counts), p95=sorted(counts)[math.ceil(.95*len(counts))-1], worst=max(counts), payload_bits=sum(r['selection_bits'] for r in covered), character_selections=sum(r['single_character_selections'] for r in covered), character_fraction=sum(r['single_character_selections'] for r in covered)/sum(counts), packet_bytes=sum(r['packet_bytes'] for r in covered), framing_bytes=41*len(covered), padding_bits=sum(r['padding_bits'] for r in covered), package_bytes=len(dictionary)+sum(r['packet_bytes'] for r in covered), whole_solution_entries=sum(r['whole_solution_entries'] for r in covered))
        profiles.append(profile)
    result = {'schema':'gamma.assigned5.literal-measurement.v1', 'contract_sha256':sha((D/'contract.json').read_bytes()), 'phase':output_name, 'rows':rows, 'profiles':profiles, 'elapsed_seconds':time.monotonic()-started, 'candidate_execution':False, 'protected_data_access':False, 'verification':'exact byte reconstruction, independent forward minimum-selection oracle, packet hash/header/padding/roundtrip'}
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'phase':output_name,'elapsed_seconds':result['elapsed_seconds'],'profiles':[{k:v for k,v in p.items() if k!='reused_noncharacter_strings'} for p in profiles]},indent=2))
    return result


if __name__ == '__main__':
    measure(json.loads((D/'contract.json').read_text())['sources'], 'baseline')
