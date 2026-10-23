"""Fit-only worker; all input access follows a reviewed immutable contract."""
import argparse
import json
import os
from pathlib import Path
import resource
import signal
import sys
import time

HERE=Path(__file__).resolve().parent;LIT=HERE.parent
sys.path.insert(0,str(HERE))
import implicit
from backend import analyze,dual,measure,sha,write
import optimize


def arm(cohort,work,output,deadline):
    started=time.monotonic();folder=output/f'{cohort}-flex256';folder.mkdir();phase='preflight'
    c=json.loads((HERE/'contract.json').read_text());implicit.require_checks()
    def expired(*_):raise TimeoutError('worker whole-job deadline reached')
    signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,max(.001,deadline-started))
    try:
        assert 0<deadline-started<=c['limits']['overall_seconds']
        resource.setrlimit(resource.RLIMIT_AS,(c['limits']['address_space_bytes'],)*2)
        os.sched_setaffinity(0,set(c['limits']['arm_cores'][cohort]))
        from supervise import check_contract
        check_contract(c,work)
        write(folder/'status.json',{'phase':phase,'complete':False})
        phase='source_identity';seedroot=work/c['cohorts'][cohort]
        texts=json.loads((seedroot/'fit-sources.json').read_text());seed=json.loads((seedroot/'dictionary.json').read_text())
        assert set(texts)==set(map(str,c['fit_ids'])) and all(texts.values()) and set(''.join(texts.values()))<=set(dual.ALPHABET)
        proof=json.loads((LIT/'binding-descent-v1/evidence/results.json').read_text())
        receipt=next(a for a in proof['arms'] if a['arm']==('control' if cohort=='R' else 'scope_joint') and a['width']==8)
        for pid,text in texts.items():assert receipt['qualification'][pid]['passed'] and analyze.sha(text.encode())==receipt['per_problem'][pid]['source_sha256']
        parent_public=json.loads((LIT/c['parent_evidence']).read_text())
        public_arm=next(a for a in parent_public['arms'] if a['cohort']==cohort)
        private_parent=json.loads((work/c['parent_private_results']).read_text())
        prior=next(a for a in private_parent['arms'] if a['cohort']==cohort)
        assert private_parent['complete'] and prior['complete'] and not prior['validation_loaded']
        assert prior['fit_source_sha256']==public_arm['fit_source_sha256']==c['private_files'][c['cohorts'][cohort]+'/fit-sources.json']
        old_q=json.loads((work/c['parent_q'][cohort]).read_text())
        assert prior['optimization']['certificate']['q_sha256']==public_arm['optimization']['certificate']['q_sha256']==sha(work/c['parent_q'][cohort])
        for key in optimize.CERT_KEYS:assert prior['optimization']['certificate'][key]==public_arm['optimization']['certificate'][key]
        phase='index';write(folder/'status.json',{'phase':phase,'complete':False});pool_started=time.monotonic()
        banned=dual.sel.forbidden_strings(texts);index=implicit.Index(texts,banned);pool_seconds=time.monotonic()-pool_started
        assert index.distinct_allowed_entries==public_arm['pool_entries'] and len(index.base.groups)==public_arm['implicit_groups']
        phase='optimization';write(folder/'status.json',{'phase':phase,'complete':False})
        def trace(row):
            row['validation_loaded']=False
            with (folder/'trace.jsonl').open('a') as f:f.write(json.dumps(row,sort_keys=True)+'\n');f.flush()
            if row['event']!='ascent' or row['iteration']%25==0:print(json.dumps({'cohort':cohort,**row}),flush=True)
        def checkpoint(q,certificate):
            write(folder/'incumbent-q.json',q);write(folder/'incumbent-certificate.json',{**certificate,'q_sha256':sha(folder/'incumbent-q.json')})
        info,q,seed,best,generated=optimize.optimize(index,seed,old_q,public_arm['optimization']['certificate'],c['pool']['capacity'],c['search'],trace,checkpoint)
        write(folder/'certificate-q.json',q);info['certificate']['q_sha256']=sha(folder/'certificate-q.json')
        phase='witnesses';write(folder/'status.json',{'phase':phase,'complete':False});witnesses={}
        for name,vocab in [('seed',seed),('best',best),('generated',generated)]:
            if vocab is None:continue
            assert len(vocab)==len(set(vocab))<=256 and not set(vocab)&banned
            witnesses[name]=measure(texts,vocab,folder/name,c['decoder_dependency_bytes'])
            assert info['certificate']['integer_lower_bound']<=witnesses[name]['objective']
        assert witnesses['best']['objective']==info['best_objective']
        result={'cohort':cohort,'mode':'flex256','fit_problems':len(texts),'complete':True,'validation_loaded':False,
                'pool_scope':c['pool']['scope'],'pool_entries':index.distinct_allowed_entries,'implicit_groups':len(index.base.groups),
                'length_pieces':len(index.pieces),'source_characters':len(index.base.positions),
                'exact_ban_occurrences':sum(len(s) for rows in index.base.banned_ends.values() for s in rows),
                'capacity':256,'mandatory_entries':0,'pool_seconds':pool_seconds,'optimization':info,'witnesses':witnesses,
                'fit_source_sha256':c['private_files'][c['cohorts'][cohort]+'/fit-sources.json'],
                'parent_q_sha256':sha(work/c['parent_q'][cohort]),'contract_sha256':sha(HERE/'contract.json'),'seconds':time.monotonic()-started}
        write(folder/'results.json',result);write(folder/'status.json',{'phase':'complete','complete':True})
    except BaseException as error:
        write(folder/'failure.json',{'phase':phase,'complete':False,'exception':type(error).__name__,
              'partial_certificates_promoted':False,'validation_loaded':False,'seconds':time.monotonic()-started});raise
    finally:signal.setitimer(signal.ITIMER_REAL,0)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--cohort',choices=('R','naming'),required=True);ap.add_argument('--work',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True);ap.add_argument('--deadline',type=float,required=True);a=ap.parse_args();arm(a.cohort,a.work,a.output,a.deadline)
