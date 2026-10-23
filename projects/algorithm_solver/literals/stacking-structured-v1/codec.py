"""Joint literal/prefix/identifier-template codec; source bytes never change."""
import base64
from functools import lru_cache
from itertools import product
import hashlib
import json
from pathlib import Path
import struct
import subprocess

HERE = Path(__file__).resolve().parent
ALPHABET = [chr(i) for i in range(32,127)] + ['\n']
canonical = lambda value: json.dumps(value, sort_keys=True, separators=(',',':'), ensure_ascii=True)


def literal(text):
    return 'L'+text


def constructor(kind, spec):
    assert kind in ('P','I')
    return kind+canonical(spec)


def order(keys):
    # D11 can omit observed characters. Never restore the full alphabet.
    alpha = {literal(c):i for i,c in enumerate(ALPHABET)}
    return sorted(set(keys), key=lambda k:(0,alpha[k],'') if k in alpha else
                  (1,0,k[1:]) if k.startswith('L') else (2,0,k))


def dictionary(keys):
    return b'STD1'+canonical([[k[0],k[1:] if k[0]=='L' else json.loads(k[1:])] for k in keys]).encode()


def literal_dictionary(keys):
    assert all(k.startswith('L') for k in keys)
    fields = [b'LTD1',struct.pack('>I',len(keys))]
    for key in keys:
        raw = key[1:].encode()
        fields += [struct.pack('>I',len(raw)),raw]
    return b''.join(fields)


def extract(texts):
    result = subprocess.run(['node',str(HERE/'extract.cjs')], input=json.dumps(texts),
                            text=True,capture_output=True,check=True)
    nodes = json.loads(result.stdout)
    for group in nodes.values():
        for kind,name in (('P','prefix'),('I','identifier')):
            for node in group[name]:
                node['key'] = constructor(kind,node['spec']) if node['spec'] else None
    return nodes


def encode_source(text, nodes, keys):
    """Minimum selections, then lexicographic IDs; P may have L/P children only."""
    keys = order(keys)
    rank = {k:i for i,k in enumerate(keys)}
    present = set(keys)
    bodies = set(nodes['bodies'])
    by_span = {(n['start'],n['end']):n for n in nodes['prefix']}

    def better(plan, incumbent):
        return incumbent is None or (len(plan['tokens']),tuple(rank[k] for k in plan['tokens'])) < (
            len(incumbent['tokens']),tuple(rank[k] for k in incumbent['tokens']))

    def lit_plan(key, start, end):
        return dict(tokens=[key],literal_spans=[(start,end,key)],prefix_codes=0,identifier_codes=0,
                    argument_codes=0,prefix_fixed_bytes=0,identifier_fixed_bytes=0,
                    repeated_identifier_bytes=0,generated_bytes=0)

    def combine(parts):
        result = {k:0 for k in ('prefix_codes','identifier_codes','argument_codes','prefix_fixed_bytes',
                                'identifier_fixed_bytes','repeated_identifier_bytes','generated_bytes')}
        result.update(tokens=[],literal_spans=[])
        for part in parts:
            result['tokens'] += part['tokens']
            result['literal_spans'] += part['literal_spans']
            for k in result:
                if k not in ('tokens','literal_spans'):
                    result[k] += part[k]
        return result

    def frontier(plans):
        # A larger generated-byte count can still have a better lexicographic
        # ID sequence. Keep it unless a <=generated plan also wins (N,IDs).
        by_generated = {}
        for plan in plans:
            value = plan['generated_bytes']
            if value not in by_generated or better(plan,by_generated[value]):
                by_generated[value] = plan
        kept = []
        champion = None
        for value, plan in sorted(by_generated.items()):
            score = (len(plan['tokens']),tuple(rank[k] for k in plan['tokens']))
            if champion is None or score < champion:
                kept.append(plan)
                champion = score
        return tuple(kept)

    @lru_cache(None)
    def expression(start,end,depth):
        key = literal(text[start:end])
        plans = [lit_plan(key,start,end)] if key in present else []
        node = by_span.get((start,end))
        if depth and node and node['key'] in present:
            children = [expression(a,b,depth-1) for a,b in node['holes']]
            if all(children):
                for choices in product(*children):
                    plan = combine(choices)
                    fixed = sum(len(part) for part in node['spec']['parts'])
                    plan['tokens'] = [node['key']]+plan['tokens']
                    plan['prefix_codes'] += 1
                    plan['argument_codes'] += len(children)
                    plan['prefix_fixed_bytes'] += fixed
                    plan['generated_bytes'] += fixed
                    if text[start:end] not in bodies and 2*plan['generated_bytes'] < len(text):
                        plans.append(plan)
        return frontier(plans)

    edges = {}
    for start,end in by_span:
        for plan in expression(start,end,8):
            if plan['tokens'][0].startswith('P'):
                edges.setdefault(start,[]).append((end,plan))
    for node in nodes['identifier']:
        key = node['key']
        args = [literal(arg) for arg in node['args']]
        if key is None or key not in present or not all(arg in present for arg in args):
            continue
        start,end = node['start'],node['end']
        spec = node['spec']
        fixed = sum(len(part) for part in spec['parts'])
        repeated = sum(len(node['args'][i]) for i in spec['uses'])-sum(map(len,node['args']))
        generated = fixed+repeated
        if text[start:end] in bodies or generated*2 >= len(text):
            continue
        plan = dict(tokens=[key]+args,literal_spans=[],prefix_codes=0,identifier_codes=1,
                    argument_codes=len(args),prefix_fixed_bytes=0,identifier_fixed_bytes=fixed,
                    repeated_identifier_bytes=repeated,generated_bytes=generated)
        edges.setdefault(start,[]).append((end,plan))
    trie = {}
    for key in keys:
        if not key.startswith('L'):
            continue
        node = trie
        for char in key[1:]:
            node = node.setdefault(char,{})
        node[None] = key
    # Minimum-length body path, then complete lexicographic IDs. Prefix
    # frontier construction already enforces each constructor-use byte cap.
    costs = [None]*(len(text)+1)
    edge = [None]*len(text)
    costs[-1] = 0
    def suffix_ids(pos):
        result = []
        while pos < len(text):
            end, plan = edge[pos]
            result.extend(rank[k] for k in plan['tokens'])
            pos = end
        return result
    for start in range(len(text)-1,-1,-1):
        options = list(edges.get(start,[]))
        node = trie
        end = start
        while end < len(text) and text[end] in node:
            node = node[text[end]]
            end += 1
            if None in node:
                options.append((end,lit_plan(node[None],start,end)))
        for end,head in options:
            if costs[end] is None:
                continue
            total = len(head['tokens'])+costs[end]
            take = costs[start] is None or total < costs[start]
            if costs[start] == total:
                old_end, old_head = edge[start]
                take = ([rank[k] for k in head['tokens']]+suffix_ids(end) <
                        [rank[k] for k in old_head['tokens']]+suffix_ids(old_end))
            if take:
                costs[start], edge[start] = total, (end,head)
    if costs[0] is None:
        raise ValueError('unencodable source')
    plans = []
    pos = 0
    while pos < len(text):
        pos, plan = edge[pos]
        plans.append(plan)
    result = combine(plans)
    result.update(selections=len(result['tokens']),
                  single_characters=sum(k.startswith('L') and len(k[1:])==1 for k in result['tokens']),
                  constructor_codes=result['prefix_codes']+result['identifier_codes'])
    result['literal_spans'].sort()
    return result


def packet(keys,tokens):
    assert 1 <= len(keys) <= 256 and len(set(keys)) == len(keys)
    index = {key:i for i,key in enumerate(keys)}
    return b'STB1'+bytes([8])+hashlib.sha256(dictionary(keys)).digest()+struct.pack('>I',len(tokens))+bytes(index[k] for k in tokens)


def decode_many(keys,plans):
    request = {'dictionary':base64.b64encode(dictionary(keys)).decode(),
               'packets':{str(pid):base64.b64encode(packet(keys,p['tokens'])).decode() for pid,p in plans.items()}}
    result = subprocess.run(['node',str(HERE/'decoder.cjs')],input=json.dumps(request),
                            text=True,capture_output=True,check=True)
    return json.loads(result.stdout)
