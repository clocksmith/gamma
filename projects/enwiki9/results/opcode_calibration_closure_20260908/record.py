"""Validate the closed calibration observation and normalize its unchanged archive."""
import hashlib
import json
import math
from pathlib import Path
import platform
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import record_driver_result as recorder
from dualstream_grammar_gate_v1 import write_json
CID='opcode_calibration_cost_v1'
JID='20260908T171535Z_9962b82f49'
JOB='operations/adaptive/completed/909_'+JID+'.json'
OUT='operations/provenance/opcode_calibration_terminal_20260908'


def read(p):return json.loads((ROOT/p).read_text())
def ref(p):return dict(path=p,sha256='sha256:'+hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def check(r):
    b=recorder.project_path(r['path']).read_bytes()
    assert hashlib.sha256(b).hexdigest()==r['sha256'].removeprefix('sha256:')
    assert 'bytes' not in r or len(b)==r['bytes']
    return b


def main():
    job=read(JOB);recorder._closed_job((ROOT/JOB).resolve(),job)
    gp=job['execution_resources']['guard_path'];g=read(gp)
    recorder._validate_guard_receipt(ROOT/gp,job,g);recorder._guard_identity(job,g)
    assert g['status']!='running' and g['returncode']==0 and not any(g['guards'].values())
    sp='results/'+CID+'/stage-decision.json';mp='results/'+CID+'/artifacts.json'
    s=read(sp);manifest=read(mp)
    assert s['status']=='passed' and s['correctness_pass'] and s['frozen_inputs_reverified'] and manifest['complete']
    for row in manifest['files']:check(row)
    raw=check(s['input']);a=s['artifacts'];arc=check(a['archive'])
    assert raw==check(a['restored']) and arc==check(a['repeat'])
    assert s['archive_saving_bytes']==0 and len(s['commands'])==3
    audits=[read('results/'+CID+'/'+x+'.audit.json') for x in ('encode','decode','repeat')]
    assert audits[0]==audits[1]==audits[2]==s['audit']
    audit=audits[0];rows=audit['rows']
    assert audit['observed_bits']==sum(r['bits'] for r in rows)==8*audit['parent']['modeled_bytes']
    excess=math.fsum(r['sse_excess_bits'] for r in rows if r['mode']==0)
    assert math.isfinite(excess) and excess==audit['literal_sse_excess_bits']==s['literal_sse_excess_bits']
    revision=dict(candidateId=CID,candidateTreeSha256=job['candidate_tree_sha256'],receipt=job['candidate_revision'])
    terminal=dict(schema='gamma.enwiki9.opcode-calibration-terminal.v1',candidate_id=CID,
        job=ref(JOB),guard=ref(gp),stage=ref(sp),artifact_manifest=ref(mp),experiment=job['experiment'],
        candidate_revision=revision,target_complete_bytes=90000000,population=s['input'],
        measurements=dict(correctness_pass=True,literal_sse_excess_bits=excess,archive_saving_bytes=0,
                          coded_literal_bits=audit['coded_literal_bits'],observed_bits=audit['observed_bits']),
        archive_bytes=len(arc),rows=rows,diagnostic_event_sha256=audit['diagnostic_event_sha256'],
        interpretation='current-SSE-hurts-fixed-parse-literals' if excess>0 else 'current-SSE-helps-or-ties-fixed-parse-literals',
        guard_flags=g['guards'],guard_peaks=g['peaks'],complete_package_bytes=None,full_corpus_score_bytes=None,
        objective_credit_bytes=0,limits=['Observation only; actual archive is unchanged.',
          'Copied-bit losses are hypothetical, excluded from the aggregate decision.',
          'Floating-point log-loss estimates are not a rigorous code-length certificate.',
          'A separately executed ablation may change copy selection; this statistic is not its archive saving.',
          'Development population only; no field-subset selection, transfer, or full-corpus projection.'])
    resources=[x.get('codec_resources') for x in s['commands']]
    result=dict(schema='gamma.enwiki9.driver-result.v2',program_id=CID,program_name='Unchanged parent calibration observation',
        arm='K',candidate_revision=revision,timestamp=job['finished_at'],run_source=JOB,
        data_path=s['input']['path'],data_size=len(raw),data_sha256=hashlib.sha256(raw).hexdigest(),data_md5=hashlib.md5(raw).hexdigest(),
        compressed_size=len(arc),compressed_sha256=hashlib.sha256(arc).hexdigest(),compressed_md5=hashlib.md5(arc).hexdigest(),
        roundtrip_ok=True,determinism=dict(scope='single-host',single_host_byte_equal=True),shared_state_synchronization=True,
        bits_per_byte=len(arc)*8/len(raw),compress_time_s=resources[0]['elapsed_seconds'] if resources[0] else None,
        decompress_time_s=resources[1]['elapsed_seconds'] if resources[1] else None,
        run_time_s=sum(c['elapsed_seconds'] for c in s['commands']),phase_resources=dict(zip(('encode','decode','repeat'),resources)),
        memory_kib=dict(peak=max((r['peak_process_rss_kib'] for r in resources if r),default=None)),
        host=dict(machine=platform.machine(),node=platform.node(),python=platform.python_version(),system=platform.system()),
        run_purpose='diagnostic',execution_mode='discovery',timing_authority='diagnostic',run_scope_label='opening250KB-calibration-observation',
        run_tags=['calibration','unchanged-parent','diagnostic'],run_context='Fixed-parse pre/post calibration attribution, not a compression mutation.',
        program_size=None,hutter_score=None,complete_package_bytes=None,full_corpus_score_bytes=None,score_accounting_complete=False,
        prize_claimable=False,qualification_status='not-certified',resource_evidence_complete=False,
        closed_guard=ref(gp),source_stage=ref(sp),artifacts=a,
        missing_diagnostics=[x for c in s['commands'] for x in c.get('missing_diagnostics',[])])
    assert not (ROOT/OUT).exists() and not (ROOT/(OUT+'.json')).exists()
    (ROOT/OUT).mkdir();write_json(ROOT/(OUT+'.json'),terminal);write_json(ROOT/(OUT+'/K.json'),result)
    write_json(ROOT/(OUT+'/index.json'),dict(schema='gamma.enwiki9.terminal-result-index.v1',job=ref(JOB),guard=ref(gp),
        evidence=[ref(OUT+'.json'),ref(sp),ref(mp)],arms=[dict(arm='K',result=ref(OUT+'/K.json'),artifacts=a)]))
    print(json.dumps(dict(terminal=OUT+'.json',literal_sse_excess_bits=excess,reflection_required=True)))


if __name__=='__main__':main()
