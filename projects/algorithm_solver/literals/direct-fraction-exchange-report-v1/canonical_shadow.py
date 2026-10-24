"""Post-acceptance, source-fixed min-F/min-N replay; no dictionary optimization."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import signal
import statistics
import struct
import sys
import time

HERE=Path(__file__).resolve().parent;LIT=HERE.parent;PRIMARY=LIT/'direct-fraction-exchange-v1'
SECONDS=1200;MEMORY=8*1024**3;CORES={6,7}
POLICIES={'min_F':'minimum_F_then_minimum_N_then_full_entry_ID_sequence',
          'canonical_min_N':'minimum_N_then_full_entry_ID_sequence_no_character_tiebreak'}
class HardDeadline(BaseException):pass

def require_checks():
    if not __debug__ or sys.flags.optimize or 'PYTHONOPTIMIZE' in os.environ:raise RuntimeError('Normal assertions required')

sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
hashbytes=lambda b:hashlib.sha256(b).hexdigest()
read=lambda p:json.loads(Path(p).read_text())

def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(path.name+'.pending')
    with tmp.open('w') as stream:json.dump(value,stream,sort_keys=True,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    tmp.replace(path)

def numeric(value,maximum):
    assert type(value) in (int,float) and math.isfinite(value) and 0<=value<=maximum
    return value

def quantiles(values):
    values=sorted(values);assert values
    return {'n':len(values),'total':sum(values),'median':statistics.median(values),
      'p90':values[math.ceil(.9*len(values))-1],'p95':values[math.ceil(.95*len(values))-1],
      'worst':values[-1],'within_32':sum(n<=32 for n in values),'within_96':sum(n<=96 for n in values)}

def encode(text,vocab,policy):
    """Backward sliced DP with complete ID tuples, separately from search cache."""
    assert policy in POLICIES and text and len(vocab)==len(set(vocab)) and all(vocab)
    best=[None]*len(text)+[(0,0,())]
    for start in range(len(text)-1,-1,-1):
        options=[]
        for entry,word in enumerate(vocab):
            end=start+len(word)
            if end<=len(text) and text[start:end]==word and best[end] is not None:
                f,n,ids=best[end];options.append((f+(9 if len(word)==1 else -1),n+1,(entry,)+ids))
        if options:best[start]=min(options,key=(lambda x:(x[0],x[1],x[2])) if policy=='min_F' else (lambda x:(x[1],x[2])))
    if best[0] is None:raise ValueError('Retained dictionary does not cover source')
    f,n,ids=best[0];chars=sum(len(vocab[i])==1 for i in ids)
    assert f==10*chars-n and ''.join(vocab[i] for i in ids)==text
    return {'F':f,'C':chars,'N':n,'ids':ids}

def dictionary_bytes(vocab):
    assert vocab==sorted(vocab) and 1<=len(vocab)==len(set(vocab))<=256 and all(vocab)
    return b'LTD1'+struct.pack('>I',len(vocab))+b''.join(struct.pack('>I',len(w.encode()))+w.encode() for w in vocab)

def packet(ids,dictionary):return b'LTV1\x08'+hashlib.sha256(dictionary).digest()+struct.pack('>I',len(ids))+bytes(ids)

def decode(blob,dictionary,vocab):
    assert blob[:5]==b'LTV1\x08' and blob[5:37]==hashlib.sha256(dictionary).digest()
    ids=tuple(blob[41:]);assert len(blob)>=41 and int.from_bytes(blob[37:41],'big')==len(ids) and all(i<len(vocab) for i in ids)
    return ''.join(vocab[i] for i in ids),ids

def measure(texts,vocab,decoder_bytes,policy,stored=None):
    binary=dictionary_bytes(vocab);rows={}
    if stored is not None:
        assert policy=='min_F' and (stored/'dictionary.bin').read_bytes()==binary
        assert {p.stem for p in (stored/'packets').glob('*.bin')}==set(texts)
    for pid,text in sorted(texts.items()):
        got=encode(text,vocab,policy);blob=packet(got['ids'],binary)
        if stored is not None:assert (stored/'packets'/f'{pid}.bin').read_bytes()==blob
        rebuilt,ids=decode(blob,binary,vocab);assert rebuilt==text and ids==got['ids']
        rows[pid]={'source_sha256':hashbytes(text.encode()),'source_utf8_bytes':len(text.encode()),
          'F':got['F'],'C':got['C'],'N':got['N'],'actions':got['N']+1,'packet_sha256':hashbytes(blob),'packet_bytes':len(blob),
          'one_program_package_bytes':len(binary)+len(blob),'one_program_package_with_decoder':len(binary)+len(blob)+decoder_bytes}
    n=sum(r['N'] for r in rows.values());chars=sum(r['C'] for r in rows.values());total=len(binary)+sum(r['packet_bytes'] for r in rows.values())
    return {'policy':POLICIES[policy],'F':10*chars-n,'C':chars,'N':n,'actions':n+len(rows),'character_fraction':chars/n,
      'selections':quantiles([r['N'] for r in rows.values()]),'action_distribution':quantiles([r['actions'] for r in rows.values()]),
      'entries':len(vocab),'character_entries':sum(len(w)==1 for w in vocab),'dictionary_bytes':len(binary),
      'packet_bytes':total-len(binary),'package_bytes':total,'decoder_source_bytes':decoder_bytes,'package_with_decoder_sources':total+decoder_bytes,
      'framing_bytes':41*len(rows),'payload_bits':8*n,'padding_bits':0,'source_utf8_bytes':sum(r['source_utf8_bytes'] for r in rows.values()),
      'amortized_package_bytes':total/len(rows),'amortized_package_with_decoder':(total+decoder_bytes)/len(rows),'per_problem':rows}

def check_primary_measure(got,old):
    assert (got['F'],got['C'],got['N'])==(old['objective'],old['characters'],old['selections']['total'])
    for key in ('character_fraction','entries','character_entries','dictionary_bytes','package_bytes','package_with_decoder_sources','framing_bytes','payload_bits','padding_bits','amortized_package_bytes'):
        assert got[key]==old[key]
    assert got['selections']==old['selections'] and got['action_distribution']==old['actions']
    assert set(got['per_problem'])==set(old['per_problem'])
    for pid,row in got['per_problem'].items():
        previous=old['per_problem'][pid]
        assert (row['F'],row['C'],row['N'])==(previous['objective'],previous['characters'],previous['selections'])
        for key in ('source_sha256','actions','packet_sha256','packet_bytes','one_program_package_bytes'):assert row[key]==previous[key]
        assert row['one_program_package_with_decoder']==previous['one_program_with_decoder']

def deltas(after,before):
    return {**{key:after[key]-before[key] for key in ('F','C','N','actions','character_fraction','package_bytes','package_with_decoder_sources')},
            **{key+'_N':after['selections'][key]-before['selections'][key] for key in ('median','p90','p95','worst')}}

def accepted_primary(directory,contract_hash):
    """Gate before any run/source/dictionary/private path is opened."""
    assert not list(directory.glob('*failure.json')) and not list(directory.glob('*/*failure.json'))
    result=read(directory/'results.json');supervisor=read(directory/'supervisor.json')
    assert result['complete'] is True and result['validation_loaded'] is False and result['contract_sha256']==contract_hash
    assert result['population']=='fixed300_fit_only' and result['m1_qualification'] is False
    assert supervisor['complete'] is True and supervisor['phase']=='report' and supervisor['contract_sha256']==contract_hash
    assert supervisor['returncodes']==[0,0] and all(type(v) is int for v in supervisor['returncodes'])
    numeric(supervisor['elapsed'],1210);numeric(supervisor['cleanup_seconds'],10)
    assert [a['cohort'] for a in result['arms']]==['R','naming']
    assert all(a['complete'] is True and a['validation_loaded'] is False and a['contract_sha256']==contract_hash for a in result['arms'])
    return result

def runtime(config):
    assert config['active'] is True and config['population']=='fixed300_fit_only'
    assert str(Path(sys.executable).absolute())==config['python_bin']
    for rel,digest in config['code_hashes'].items():assert sha(LIT/rel)==digest,rel
    for path,digest in config['runtime_files'].items():assert sha(path)==digest,path
    assert len(config['fit_ids'])==len(set(config['fit_ids']))==300
    assert set(config['decoder_source_files'])=={'literals.py','pass2/working/bitpack.py'}
    total=0
    for rel,receipt in config['decoder_source_files'].items():
        path=LIT/rel;assert sha(path)==receipt['sha256'] and path.stat().st_size==receipt['bytes'];total+=path.stat().st_size
    assert total==config['decoder_dependency_bytes']

def replay(work,run,primary_directory,config):
    ch=sha(PRIMARY/'contract.json');accepted=accepted_primary(primary_directory,ch)
    # All private access is below the accepted-independent-primary gate.
    runtime(config)
    assert not list(run.glob('*failure.json')) and not list(run.glob('*/*failure.json'))
    raw=read(run/'results.json');assert sha(run/'results.json')==accepted['private_results_sha256']
    assert raw['complete'] is True and raw['validation_loaded'] is False and raw['contract_sha256']==ch
    assert sha(run/'supervisor.json')==accepted['production_supervisor_sha256']
    parent_path=LIT/config['parent_contract'];assert sha(parent_path)==config['parent_contract_sha256'];parent=read(parent_path)
    qualification=read(LIT/'binding-descent-v1/evidence/results.json');arms=[]
    assert [a['cohort'] for a in raw['arms']]==['R','naming']
    for old,approved in zip(raw['arms'],accepted['arms']):
        cohort=old['cohort'];folder=run/cohort
        assert old==read(folder/'results.json') and sha(folder/'results.json')==approved['private_arm_result_sha256']
        assert old['bindings']==approved['bindings'] and old['final_incumbent']==approved['final_incumbent']
        rel=parent['cohorts'][cohort]+'/fit-sources.json';sourcefile=work/rel
        assert sha(sourcefile)==config['private_files'][rel]==approved['bindings']['source_sha256']
        texts=read(sourcefile);assert set(texts)==set(map(str,config['fit_ids']))
        receipt=next(a for a in qualification['arms'] if a['width']==8 and a['arm']==('control' if cohort=='R' else 'scope_joint'))
        for pid,text in texts.items():
            assert type(text) is str and text and receipt['qualification'][pid]['passed'] is True
            assert hashbytes(text.encode())==receipt['per_problem'][pid]['source_sha256']
        witnesses={}
        for name,index in (('seed',0),('final',old['final_incumbent'])):
            target=folder/'incumbents'/f'{index:03d}';metadata=old['incumbents'][index]['witness'];assert old['incumbents'][index]['index']==index
            vocab=read(target/'dictionary.json');assert sha(target/'dictionary.json')==metadata['dictionary_sha256']
            assert sha(folder/'retained-dictionaries'/f'{index:03d}.json')==metadata['dictionary_sha256']
            minf=measure(texts,vocab,config['decoder_dependency_bytes'],'min_F',target);check_primary_measure(minf,metadata)
            canonical=measure(texts,vocab,config['decoder_dependency_bytes'],'canonical_min_N')
            assert canonical['N']<=minf['N'] and minf['F']<=canonical['F']
            witnesses[name]={'incumbent':index,'sorted_dictionary_sha256':metadata['dictionary_sha256'],
              'min_F':minf,'canonical_min_N':canonical,'canonical_minus_min_F':deltas(canonical,minf)}
        arms.append({'cohort':cohort,'source_sha256':sha(sourcefile),'fit_problems':len(texts),
          'original_parent_seed_dictionary_sha256':approved['references']['seed']['original_parent_dictionary_sha256'],
          'witnesses':witnesses,'final_minus_seed':{policy:deltas(witnesses['final'][policy],witnesses['seed'][policy]) for policy in POLICIES}})
    return {'schema':'gamma.direct-fraction-exchange.canonical-shadow.v1','complete':True,'auxiliary_only':True,
      'validation_loaded':False,'optimization_performed':False,'m1_qualification':False,'population':'fixed300_fit_only',
      'contract_sha256':ch,'accepted_primary_report_sha256':sha(primary_directory/'results.json'),
      'accepted_primary_supervisor_sha256':sha(primary_directory/'supervisor.json'),'private_results_sha256':sha(run/'results.json'),
      'auxiliary_code_sha256':sha(HERE/'canonical_shadow.py'),
      'auxiliary_file_sha256':{name:sha(HERE/name) for name in ('canonical_shadow.py','test_canonical_shadow.py','CANONICAL-REPORTING-NOTE.md')},'arms':arms,
      'policy_scope':'Same retained sorted literal IDs for both policies. Historical parent ID order is not reused. No character-count tie break under canonical min-N.',
      'interpretation':'Encoding-policy comparison only. No search, source change, candidate selection, qualification or promotion. Lower min-F does not establish lower canonical fraction.'}

def markdown(result):
    if not result['complete']:return '# Canonical policy comparison\n\nNo verdict: auxiliary replay or publication incomplete. The accepted primary result is unchanged.\n'
    lines=['# Item44 canonical policy comparison','',result['interpretation'],'',result['policy_scope'],'',
      '| Cohort / dictionary / policy | F | C | N | Actions | C/N | Median / p90 / p95 N | Full package bytes |',
      '| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |']
    for arm in result['arms']:
        for name,pair in arm['witnesses'].items():
            for policy in POLICIES:
                w=pair[policy];q=w['selections'];lines.append(f"| {arm['cohort']} / {name} / {policy} | {w['F']} | {w['C']} | {w['N']} | {w['actions']} | {w['character_fraction']:.6f} | {q['median']} / {q['p90']} / {q['p95']} | {w['package_with_decoder_sources']} |")
    lines+=['','results.json contains every source-bound row, signed final-minus-seed and policy deltas, action distributions, and separate dictionary, packet, framing and decoder charges. Canonical packets are independently constructed/decoded in memory; source strings, dictionary literals and ID sequences are not published.']
    return '\n'.join(lines)+'\n'

def withdraw(output,reason):
    failed={'complete':False,'auxiliary_only':True,'validation_loaded':False,'failure_reason':reason,'primary_result_changed':False}
    output.mkdir(parents=True,exist_ok=True)
    for name,text in (('results.json',json.dumps(failed,sort_keys=True)+'\n'),('REPORT.md',markdown(failed))):
        path=output/name
        try:
            temp=output/(name+'.failure');temp.write_text(text);temp.replace(path)
        except BaseException:
            try:path.unlink(missing_ok=True)
            except BaseException:pass

def publish(result,output):
    try:
        write(output/'results.json.staged',result);(output/'REPORT.md.staged').write_text(markdown(result))
        (output/'REPORT.md.staged').replace(output/'REPORT.md');(output/'results.json.staged').replace(output/'results.json')
    except BaseException:withdraw(output,'publication_failure');raise

def main(work,run,primary_directory,output):
    started=time.monotonic();phase='setup';may_write=False
    def expired(*_):raise HardDeadline('Auxiliary whole-job deadline')
    signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,SECONDS)
    try:
        require_checks();resource.setrlimit(resource.RLIMIT_AS,(MEMORY,MEMORY));os.sched_setaffinity(0,CORES)
        destination=output.resolve()
        for protected in (run.resolve(),primary_directory.resolve(),PRIMARY.resolve()):
            if destination==protected or destination.is_relative_to(protected) or protected.is_relative_to(destination):
                raise ValueError('Auxiliary destination overlaps a primary input')
        if destination==work.resolve() or work.resolve().is_relative_to(destination) or destination==HERE.resolve():
            raise ValueError('Auxiliary destination overlaps source or code root')
        may_write=True
        if output.exists():raise FileExistsError('Fresh auxiliary output required')
        output.mkdir(parents=True,exist_ok=False);config=read(PRIMARY/'contract.json');phase='accepted_primary_gate_and_replay'
        result=replay(work,run,primary_directory,config)
        result['seconds']=numeric(time.monotonic()-started,SECONDS);result['peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        assert result['peak_rss_kib']*1024<=MEMORY
        result['limits']={'whole_seconds':SECONDS,'address_space_bytes':MEMORY,'cores':sorted(CORES)}
        phase='publication';publish(result,output);numeric(time.monotonic()-started,SECONDS)
    except BaseException as error:
        if not may_write:raise
        try:write(output/'failure.json',{'complete':False,'phase':phase,'exception':type(error).__name__,'seconds':time.monotonic()-started})
        finally:withdraw(output,'auxiliary_failure')
        raise
    finally:signal.setitimer(signal.ITIMER_REAL,0)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--work',type=Path,required=True);ap.add_argument('--run',type=Path,required=True)
    ap.add_argument('--primary-report',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    main(args.work,args.run,args.primary_report,args.output)
