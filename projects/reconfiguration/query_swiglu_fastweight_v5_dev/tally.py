"""Per-arm counts for one development receipt. Usage: python -I tally.py RECEIPT_JSON [ARM,ARM REGIME]"""
import json, sys, collections
d = json.load(open(sys.argv[1]))
print(d['model'], 'layers', d.get('targetLayers'), 'rows', len(d['rows']))
c = collections.defaultdict(lambda: [0, 0, 0, 0, 0, 0])
for x in d['rows']:
    multi = '-' in x['expected']
    v = c[(x['regime'], x['arm'])]
    v[0 if not multi else 2] += 1
    v[1 if not multi else 3] += x['correct']
    v[4] += (x['text'].strip() == '')
    v[5] += x['truncated']
for reg in ('bare', 'context'):
    for arm in ('base', 'identity', 'no_stop', 'stop_gated'):
        v = c[(reg, arm)]
        print(f"{reg:8s}{arm:11s} total {v[1]+v[3]:2d}/24  one-token {v[1]:2d}/{v[0]}  multi {v[3]:2d}/{v[2]}  empty {v[4]:2d}  truncated {v[5]:2d}")
if len(sys.argv) > 2:
    for x in d['rows']:
        if x['arm'] in sys.argv[2].split(',') and x['regime'] == sys.argv[3]:
            print(x['task_id'], x['arm'], 'OK' if x['correct'] else '--', repr(x['expected']), repr(x['text'][:40]), x['generatedTokens'][:6])
