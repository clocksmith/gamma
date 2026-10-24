"""Supplied-text exact move scoring; no corpus loader or search runner."""
import importlib.util
import os
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('direct_fraction_parent40',HERE.parent/'fraction-primal-repair-v1/model.py')
parent=importlib.util.module_from_spec(spec);saved=list(sys.path)
try:spec.loader.exec_module(parent)
finally:sys.path[:]=saved


def require_checks():
    if not __debug__ or sys.flags.optimize or 'PYTHONOPTIMIZE' in os.environ:raise RuntimeError('assertions required')


class Graph:
    def __init__(self,texts,pool,capacity=256,banned=(),**limits):
        require_checks();self.texts=dict(sorted(texts.items()));self.pool=tuple(pool);self.capacity=capacity
        assert len(self.pool)==len(set(self.pool)) and all(self.pool) and not set(self.pool)&set(banned)
        assert self.pool==tuple(sorted(self.pool)),'canonical pool order'
        assert type(capacity) is int and 0<capacity<=256
        self.ids={word:i for i,word in enumerate(self.pool)}
        self.owners={word:set() for word in self.pool}
        self.rows={pid:[[] for _ in text] for pid,text in self.texts.items()}
        tails,heads,entries,sources,sinks,positions,vertices,transitions=parent.occurrences(self.texts,self.pool,**limits)
        for tail,head,entry,(pid,start) in zip(tails,heads,entries,positions):
            word=self.pool[entry];self.rows[pid][start].append((start+head-tail,word,entry,9 if len(word)==1 else -1))
            self.owners[word].add(pid)
        self.arcs=len(entries);self.transitions=transitions

    def path(self,pid,active):
        text=self.texts[pid];n=len(text);distance=[None]*n+[(0,0)];back=[None]*n
        for start in range(n-1,-1,-1):
            best=None
            for end,word,entry,cost in self.rows[pid][start]:
                if word in active and distance[end] is not None:
                    f,count=distance[end];choice=(f+cost,count+1,entry,end)
                    if best is None or choice<best:best=choice
            if best is not None:distance[start]=best[:2];back[start]=(self.pool[best[2]],best[3])
        if distance[0] is None:return None
        words=[];at=0
        while at<n:word,at=back[at];words.append(word)
        assert ''.join(words)==text
        C=sum(len(w)==1 for w in words);F,N=distance[0];assert F==10*C-N
        # Cache strings, never mutable dictionary IDs. Sorted subset IDs retain
        # the same lexical tie order and are assigned only when serializing.
        return {'F':F,'C':C,'N':N,'words':tuple(words),'used':frozenset(words)}

    def summarize(self,active,rows,recomputed):
        F=sum(row['F'] for row in rows.values());C=sum(row['C'] for row in rows.values());N=sum(row['N'] for row in rows.values())
        assert F==10*C-N and all(row['used']<=active for row in rows.values())
        dictionary_bytes=8+sum(4+len(w.encode('utf-8')) for w in active)
        # Fixed eight-bit packet: N payload bytes plus 41 framing/Finish bytes
        # per source, unchanged at 249..256 entries. Decoder term is constant.
        package_bytes=dictionary_bytes+N+41*len(rows)
        return {'active':frozenset(active),'rows':rows,'F':F,'C':C,'N':N,
                'dictionary_bytes':dictionary_bytes,'package_bytes':package_bytes,
                'objective':(F,N,package_bytes),'order':tuple(sorted(active)),
                'eligible':len(active)<=self.capacity,'recomputed_programs':recomputed}

    def initial(self,active):
        active=frozenset(active);assert active<=set(self.pool) and len(active)<=self.capacity
        rows={pid:self.path(pid,active) for pid in self.texts}
        if any(row is None for row in rows.values()):raise ValueError('seed coverage failure')
        return self.summarize(active,rows,len(rows))

    def evaluate(self,current,add=(),remove=(),ranking=False):
        add=frozenset(add);remove=frozenset(remove);old=current['active']
        assert current['eligible'] and add<=set(self.pool)-old and remove<=old and not add&remove
        active=(old-remove)|add
        assert len(active)<=self.capacity+int(ranking)
        assert not ranking or (len(add)==1 and not remove),'ranking only a single addition'
        affected=set().union(*(self.owners[word] for word in add)) if add else set()
        affected.update(pid for pid,row in current['rows'].items() if row['used']&remove)
        rows=current['rows'].copy()
        for pid in sorted(affected):
            rows[pid]=self.path(pid,active)
            if rows[pid] is None:return None,{'coverage_failure':True,'affected_programs':len(affected)}
        return self.summarize(active,rows,len(affected)),{'coverage_failure':False,'affected_programs':len(affected)}

    @staticmethod
    def accept(current,candidate):
        assert candidate is not None and candidate['eligible'] and candidate['objective']<current['objective']
        return candidate
