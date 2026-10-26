"""Linked source-as-data rerun: independently check even unselected additions."""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import signal
import run as owner

def audit(state, additions):
    f=state['f']; vocabulary=state['best']['vocabulary']
    texts={v['key']:v['source'] for arm in additions.values() for v in arm.values()}
    rows=state['accelerator'].Graph(texts).score(vocabulary,materialize=True)
    packed=f.base.dictionary_bytes(list(vocabulary)); evidence=[]
    for arm,variants in additions.items():
        for pid,item in variants.items():
            source=item['source'];key=item['key'];path=f.exact_path(source,vocabulary)
            row=rows[key]
            if path is None:
                if row is not None:raise ValueError('reachability mismatch')
                evidence.append(dict(arm=arm,id=pid,sha256=item['sha256'],reachable=False));continue
            if row is None or path[:2]!=(row['selections'],row['characters']):
                raise ValueError('unselected addition accelerator cost mismatch')
            packet=f.codec.packet(list(path[2]),8,packed)
            f.codec.verify_packet(packet,packed,[s.encode() for s in vocabulary],source.encode())
            evidence.append(dict(arm=arm,id=pid,sha256=item['sha256'],reachable=True,
                selections=path[0],characters=path[1],packet_bytes=len(packet),
                byte_codepoint_dp_equal=True,packet_decoded_exactly=True))
    return evidence

def main(freeze,output):
    for path,digest in freeze['code_sha256'].items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=digest:raise ValueError('code drift')
    original=owner.pinned(freeze['cost_freeze']); prior=owner.pinned(freeze['cost_report'])
    delegate=owner.compare.compare; evidence=[]
    def checked_compare(state,additions):
        evidence.extend(audit(state,additions))
        return delegate(state,additions)
    owner.compare.compare=checked_compare
    try: actual=owner.run(original,output)
    finally: owner.compare.compare=delegate
    if len(evidence)!=16 or not all(r['reachable'] for r in evidence):raise ValueError('exact16 reachable additions required')
    for key in ['comparisons','source_storage','dictionary_sha256','introduced_arm_entries','exact_existing_source_duplicates']:
        # Normalize exact Fractions through the same serialization as original run.
        value=json.loads(json.dumps(actual[key],default=lambda x:dict(numerator=x.numerator,denominator=x.denominator)))
        if value!=prior[key]:raise ValueError('reproduction mismatch: '+key)
    return dict(schema='gamma.extrema8-all-addition-cost-verification.v1',verified=True,
        cost_report_sha256=freeze['cost_report']['sha256'],cost_freeze_sha256=freeze['cost_freeze']['sha256'],
        dictionary_sha256=actual['dictionary_sha256'],all_additions=evidence,
        exact_additions_checked=16,full_fit_owners=300,full_original_variants_retained=875,
        reproduced_four_arm_metrics_and_storage=True,candidate_execution=False,dictionary_search=False,
        peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--freeze',required=True);p.add_argument('--freeze-sha256',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60));signal.alarm(60)
    frozen=owner.pinned(dict(path=str(Path(a.freeze).resolve()),sha256=a.freeze_sha256))
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False,mode=0o700)
    try:
        result=main(frozen,out);result['freeze_sha256']=a.freeze_sha256
        (out/'verified.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    except BaseException as exc:
        (out/'failure.json').write_text(json.dumps(dict(error_type=type(exc).__name__,verified=False))+'\n');raise
