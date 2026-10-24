"""Supplied-input canonical fraction scorer; no corpus loader or experiment runner."""
from fractions import Fraction
import importlib.util
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('canonical_fraction_parent44',HERE.parent/'direct-fraction-exchange-v1/mechanism.py')
parent=importlib.util.module_from_spec(spec);saved=list(sys.path)
try:spec.loader.exec_module(parent)
finally:sys.path[:]=saved


def objective(C,N,package):
    assert type(C) is int and type(N) is int and 0<=C<=N and N>0
    assert type(package) is int and package>=0
    return Fraction(C,N),N,package


class Graph(parent.Graph):
    def __init__(self,texts,pool,seed,capacity=256,banned=(),decoder_bytes=0,**limits):
        assert type(decoder_bytes) is int and decoder_bytes>=0
        self.decoder_bytes=decoder_bytes
        super().__init__(texts,pool,capacity,banned,**limits)
        seed=frozenset(seed);assert seed<=set(self.pool) and 0<len(seed)<=capacity
        rows={pid:self.path(pid,seed) for pid in self.texts}
        if any(row is None for row in rows.values()):raise ValueError('uncovered seed')
        self.caps={pid:row['N'] for pid,row in rows.items()}
        self.seed=self.summarize(seed,rows,len(rows))

    def path(self,pid,active):
        text=self.texts[pid];n=len(text);distance=[None]*n+[0];back=[None]*n
        for start in range(n-1,-1,-1):
            best=None
            for end,word,entry,_ in self.rows[pid][start]:
                if word in active and distance[end] is not None:
                    choice=(distance[end]+1,entry,end)
                    if best is None or choice<best:best=choice
            if best is not None:distance[start]=best[0];back[start]=best[1:]
        if distance[0] is None:return None
        ids=[];words=[];at=0
        while at<n:
            entry,at=back[at];ids.append(entry);words.append(self.pool[entry])
        assert ''.join(words)==text and distance[0]==len(words)
        return {'N':len(words),'C':sum(len(w)==1 for w in words),'words':tuple(words),
                'pool_ids':tuple(ids),'used':frozenset(words)}

    def summarize(self,active,rows,recomputed):
        assert set(rows)==set(self.texts) and all(r['used']<=active for r in rows.values())
        C=sum(r['C'] for r in rows.values());N=sum(r['N'] for r in rows.values())
        db=8+sum(4+len(w.encode()) for w in active);package=db+41*len(rows)+N+self.decoder_bytes
        failures=tuple(pid for pid,row in rows.items() if row['N']>self.caps[pid])
        return {'active':frozenset(active),'rows':rows,'C':C,'N':N,'dictionary_bytes':db,
                'raw_package_bytes':package-self.decoder_bytes,'full_package_bytes':package,
                'objective':objective(C,N,package),'order':tuple(self.ids[w] for w in sorted(active)),
                'cap_failures':failures,'eligible':len(active)<=self.capacity and not failures,
                'recomputed_programs':recomputed}

    def evaluate(self,current,add=(),remove=(),ranking=False):
        add=frozenset(add);remove=frozenset(remove);old=current['active']
        assert current['eligible'] and add<=set(self.pool)-old and remove<=old and not add&remove
        active=(old-remove)|add
        assert len(active)<=self.capacity+int(ranking)
        assert not ranking or len(add)==1 and not remove
        affected=set().union(*(self.owners[w] for w in add)) if add else set()
        affected.update(pid for pid,row in current['rows'].items() if row['used']&remove)
        rows=current['rows'].copy();recomputed=0
        receipt={'affected_programs':len(affected),'recomputed_programs':0,'coverage_failure':False,'cap_failures':[]}
        for pid in sorted(affected):
            rows[pid]=self.path(pid,active);recomputed+=1;receipt['recomputed_programs']=recomputed
            if rows[pid] is None:receipt['coverage_failure']=True;return None,receipt
        result=self.summarize(active,rows,recomputed);receipt['cap_failures']=list(result['cap_failures'])
        return result,receipt


def sweep(graph,current,shortlist_size=4):
    """One complete invented-data epoch, immutable incumbent; no time/corpus API."""
    opportunities=[];counters={kind:{'attempted':0,'coverage_failures':0,'cap_failures':0,'recomputed_programs':0}
                               for kind in ('add','remove','swap','rescore')}
    best=current;scores=[]
    def probe(kind,add=(),remove=()):
        nonlocal best
        result,receipt=graph.evaluate(current,add,remove,ranking=kind=='add' and len(current['active'])==graph.capacity)
        opportunities.append((kind,tuple(graph.ids[w] for w in add),tuple(graph.ids[w] for w in remove)))
        row=counters[kind];row['attempted']+=1;row['coverage_failures']+=receipt['coverage_failure']
        row['cap_failures']+=bool(receipt['cap_failures']);row['recomputed_programs']+=receipt['recomputed_programs']
        if result is not None and result['eligible'] and (result['objective'],result['order'])<(best['objective'],best['order']) and result['objective']<current['objective']:
            best=result
        return result
    for word in graph.pool:
        if word not in current['active']:
            result=probe('add',(word,));assert result is not None and not result['cap_failures']
            scores.append((result['objective'],graph.ids[word],word))
    shortlist=[word for _,_,word in sorted(scores)[:shortlist_size]]
    for word in sorted(current['active']):probe('remove',remove=(word,))
    for add in shortlist:
        for remove in sorted(current['active']):probe('swap',(add,),(remove,))
    # Always one full rescore, including a non-improving incumbent, in this
    # complexity fixture. A production protocol must charge each retention rescore.
    checked=graph.initial(best['active']);counters['rescore']['attempted']=1;counters['rescore']['recomputed_programs']=len(graph.texts)
    assert checked['rows']==best['rows'] and checked['objective']==best['objective'] and checked['eligible']
    return checked,{'counters':counters,'shortlist_ids':[graph.ids[w] for w in shortlist],
                    'opportunities':opportunities,'strict_improvement':checked['objective']<current['objective']}
