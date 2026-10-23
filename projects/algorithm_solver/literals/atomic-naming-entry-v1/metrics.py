"""Exact scalar accounting. Missing coverage retains denominator; quantiles label the covered subset."""
from collections import Counter
import core as c

POLICIES=('canonical','shortest_min_char')

def aggregate(rows,ids,db,decoder):
    selected=[rows[str(pid)] for pid in ids];good=[r for r in selected if r['encodable']]
    n=sum(r['selections'] for r in good);chars=sum(r['single_characters'] for r in good)
    package=db+sum(r['packet_bytes'] for r in good)
    return {'distribution_scope':'all programs' if len(good)==len(ids) else 'covered programs only; incomplete denominator',
            'coverage_complete':len(good)==len(ids),'problems':len(ids),'covered':len(good),'failed_ids':[str(pid) for pid in ids if not rows[str(pid)]['encodable']],
            'qualified':sum(r['encodable'] and r.get('qualified_source',False) for r in selected),
            'selections':c.analyze.distribution([r['selections'] for r in good]) if good else None,
            'actions':c.analyze.distribution([r['actions'] for r in good]) if good else None,
            'single_character_codes':chars,'single_character_fraction':chars/n if n else None,
            'source_bytes':sum(r['source_bytes'] for r in selected),'framing_bytes':41*len(good),
            'payload_bits':8*n,'padding_bits':0,'package_bytes':package,
            'package_with_decoder_dependencies':package+decoder,
            'package_scope':'encoded programs only; failed programs retained in coverage denominator'}

def spelling(texts):
    recs=c.rewrite.records(texts);names=Counter();occurrences=Counter()
    for rec in recs.values():
        for v in rec['variables']:
            if v['eligible']:
                names[str(len(v['name'].encode()))]+=1;occurrences[str(len(v['name'].encode()))]+=len(v['spans'])
    return {'eligible_binding_spelling_byte_lengths':dict(names),'eligible_occurrence_spelling_byte_lengths':dict(occurrences)}
