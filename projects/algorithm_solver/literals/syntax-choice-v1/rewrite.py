"""Strict exact-cost descent over guarded AST spellings; candidates remain private."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
HERE=Path(__file__).resolve().parent;LIT=HERE.parent
sys.path.insert(0,str(LIT/'cost-decomposition-v1'));import analyze
spec=importlib.util.spec_from_file_location('syntax_choice_codec',LIT/'clusters-v1/search.py');codec=importlib.util.module_from_spec(spec);spec.loader.exec_module(codec)


class Client:
    def __init__(self):
        self.proc=subprocess.Popen(['node',str(HERE/'alternatives.cjs')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
    def proposals(self,text,vocab,mode,limit):
        self.proc.stdin.write(json.dumps({'text':text,'vocab':vocab,'mode':mode,'limit':limit})+'\n');self.proc.stdin.flush()
        line=self.proc.stdout.readline()
        if not line:raise RuntimeError('AST worker exited')
        result=json.loads(line)
        if 'error' in result:raise RuntimeError(result['error'])
        return result
    def close(self):
        self.proc.stdin.close();self.proc.wait(timeout=10);self.proc.stdout.close()
        assert self.proc.returncode==0
    def __enter__(self):return self
    def __exit__(self,*args):self.close()


def optimize(text,vocab,mode,cfg,client):
    tree=codec.trie(vocab);cost=lambda s:len(codec.encode_text(s,tree))
    current=text;value=cost(text);initial=value;trials=0;moves=[];trace=[];caps=0;stop='move_limit';unsupported=False
    for round_no in range(cfg['moves']):
        proposals=client.proposals(current,vocab,mode,cfg['proposals']);caps+=proposals['truncated']
        if proposals['unsupported']:stop='unsupported';unsupported=True;break
        best=None
        for candidate in proposals['proposals']:
            if trials>=cfg['trials']:break
            source=candidate['text'];score=cost(source);trials+=1
            trace.append({'kind':candidate['kind'],'source_sha256':analyze.sha(source.encode()),'selections':score})
            order=(score,len(source.encode()),source)
            if score<value and (best is None or order<best[0]):best=(order,candidate)
        if best is not None:
            order,candidate=best;current=candidate['text'];value=order[0]
            moves.append({'kind':candidate['kind'],'selections':value,'source_sha256':analyze.sha(current.encode())})
        if trials>=cfg['trials']:stop='trial_limit';break
        if best is None:stop='local_single_edit';break
    assert value<=initial
    return current,{'trials':trials,'moves':len(moves),'accepted':moves,'proposal_caps':caps,'stop':stop,'unsupported':unsupported,
                    'initial_selections':initial,'final_selections':value,'_trace':trace}


def rewrite_all(texts,vocab,mode,cfg):
    out={};stats={}
    with Client() as client:
        for pid,text in sorted(texts.items()):out[pid],stats[str(pid)]=optimize(text,vocab,mode,cfg,client)
    return out,stats
