"""Public-only binding and accepted54 authority checks; no corpus loader."""
import copy
import math
import re
import common as c
import adapter

P54='persistent-spelling-stack-v1/'
PUBLIC=(P54+'contract.json',P54+'evidence/results.json',P54+'evidence/production-supervisor.json',P54+'evidence/report-supervisor.json',P54+'evidence/record-time-best.json','lexfrac-v1/contract.json','lexfrac-v1/evidence/results.json')
TOP54=set('M1_gaps arms complete contract_sha256 decoded_packets decoder_dependency_bytes fresh_qualification_summary global_ban_count global_ledger_sha256 global_variant_count independent_replay model_bytes offline_encoder_bytes parent_dictionary_bindings parent_evidence peak_rss_kib predictions private_results_sha256 production_peak_rss_kib promotion_allowed ranked_passing_candidates record_time_best replay_scope replay_seconds report_ban_replay runner_seconds runtime_footprint scope search selected_successor standing_reference_evidence supervisor_seconds training_steps verdicts'.split())
ROW=set('actions encodable one_program_package_bytes one_program_package_with_decoder_dependencies packet_bytes packet_sha256 qualified_source selections single_characters source_byte_delta source_bytes source_sha256'.split())

def build():
    parent=c.read(c.LIT/PUBLIC[0]);c.shared('common').verify_public(parent)
    result={'schema':'gamma.comparator-carrier-replay.v1','active':False,'historical_only':True,
      'recorded54_commit':'187e06a09','fixed51_commit':'5389ce575','python_bin':parent['python_bin'],'work':parent['work'],
      'limits':{'worker_seconds':600,'whole_seconds':1200,'cleanup_seconds':10,'address_space_bytes':c.MEMORY,'cores':[0,1,2,3]},
      'code_hashes':copy.deepcopy(parent['code_hashes']),'runtime_files':copy.deepcopy(parent['runtime_files']),
      'authorities':{path:c.hashfile(c.LIT/path) for path in PUBLIC}}
    for path in PUBLIC:result['code_hashes'][path]=result['authorities'][path]
    for name in c.FILES:result['code_hashes'][str((c.HERE/name).relative_to(c.LIT))]=c.hashfile(c.HERE/name)
    bound=c.read(c.LIT/PUBLIC[4]);e=c.read(c.LIT/PUBLIC[-1]);p=c.read(c.LIT/PUBLIC[-2])
    assert bound['comparison']=={'kind':'external','stage':'51','arm':'flat'}
    assert bound['evidence']['sha256']==result['authorities'][PUBLIC[-1]]=='c287fe481d1bac9b505c337b5c6fa6cdd875a928ca07e3274d5efcd7808bb77a'
    assert bound['parent_contract']['sha256']==result['authorities'][PUBLIC[-2]]==e['contract_sha256']
    assert bound['recorded_commit']==result['fixed51_commit']
    result['comparator_binding']=bound
    result['private_inputs']={parent['sources']['all']['path']:parent['sources']['all']['sha256'],
      adapter.SEED:parent['dictionaries']['43N']['sha256'],bound['dictionary']['path']:bound['dictionary']['sha256'],
      bound['private_results']['path']:bound['private_results']['sha256']}
    assert len(result['private_inputs'])==4
    assert p['seed']['dictionary_sha256']==result['private_inputs'][adapter.SEED]
    assert e['arms']['flat']['dictionary_sha256']==bound['dictionary']['sha256'] and e['results_sha256']==bound['private_results']['sha256']
    result['offline_implementation_bytes']=sum((c.LIT/path).stat().st_size for path in result['code_hashes'] if path.endswith(('.py','.cjs')) and '/test_' not in path)
    # Actual public schema/lineage is exercised before a pending file can exist.
    public_inputs(result)
    return result


def public_inputs(config):
    reader=c.Reader(config)
    public={p:reader(c.LIT,p,h) for p,h in config['authorities'].items()}
    assert set(public)==set(PUBLIC)
    parent=public[PUBLIC[0]];e=public[PUBLIC[1]];r=c.shared('report')
    assert set(e)==TOP54 and e['complete'] is True and e['independent_replay'] is True
    assert e['contract_sha256']==config['authorities'][PUBLIC[0]] and e['promotion_allowed'] is False
    assert e['record_time_best']['resolved'] is False and e['predictions']['P4'] is None
    assert e['decoded_packets']==4800 and e['selected_successor'] is None
    for path,phase in ((PUBLIC[2],'production'),(PUBLIC[3],'report')):
        s=public[path];assert s['complete'] is True and type(s['exit_code']) is int and s['exit_code']==0 and s['outer_timeout'] is False
        assert s['phase']==phase and s['contract_sha256']==e['contract_sha256']
        assert type(s['elapsed']) in (int,float) and math.isfinite(s['elapsed']) and 0<=s['elapsed']<=(3600 if phase=='production' else 1800)
    assert e['parent_dictionary_bindings']==parent['dictionaries']
    assert e['standing_reference_evidence']==parent['standing_reference_evidence']
    assert e['decoder_dependency_bytes']==parent['decoder_dependency_bytes']
    # Public-only parent reconstruction; this routine never loads a private carrier.
    _,references,_=r.public_inputs(parent)
    expected={(anchor+'-'+suffix,policy) for anchor in r.ANCHORS for suffix in ('U','S') for policy in r.POLICIES}
    arms=e['arms'];assert len(arms)==len(expected) and {(a['arm'],a['policy']) for a in arms}==expected
    ids={str(i) for values in parent['partition'].values() for i in values}
    assert len(ids)==400
    for a in arms:
        assert set(a['per_problem'])==ids and set(a['qualification'])==ids
        assert a['entries']==256 and a['character_entries']==92 and a['illegal_entry_sha256']==[]
        for pid,row in a['per_problem'].items():
            assert set(row)==ROW
            assert row['encodable'] is True and row['qualified_source'] is True and a['qualification'][pid]['passed'] is True
            for key in ROW-{'encodable','qualified_source','packet_sha256','source_sha256'}:assert type(row[key]) is int
            assert row['selections']>0 and 0<=row['single_characters']<=row['selections']
            assert row['actions']==row['selections']+1 and row['packet_bytes']==41+row['selections']
            for key in ('packet_sha256','source_sha256'):assert re.fullmatch('[0-9a-f]{64}',row[key])
            assert row['one_program_package_bytes']==a['dictionary_bytes']+row['packet_bytes']
            assert row['one_program_package_with_decoder_dependencies']==row['one_program_package_bytes']+parent['decoder_dependency_bytes']
        for split,key in (('fit','dev_fit'),('validation','dev_val')):
            adapter.exact(a[split],r.aggregate(a['per_problem'],parent['partition'][key],a['dictionary_bytes'],parent['decoder_dependency_bytes']))
    assert not reader.private_reads
    return parent,e,references
