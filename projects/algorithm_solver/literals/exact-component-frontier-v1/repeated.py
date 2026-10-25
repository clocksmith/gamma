"""Linear-storage suffix/SAM shared-fragment inventory and exact residual controls."""
import itertools
import time
import frontier as f


class SuffixAutomaton:
    def __init__(self,text):
        self.edges=[{}];self.link=[-1];self.length=[0];last=0
        for c in text:
            current=len(self.edges)
            self.edges.append({});self.length.append(self.length[last]+1);self.link.append(0)
            p=last
            while p>=0 and c not in self.edges[p]:
                self.edges[p][c]=current;p=self.link[p]
            if p>=0:
                q=self.edges[p][c]
                if self.length[p]+1==self.length[q]:
                    self.link[current]=q
                else:
                    clone=len(self.edges)
                    self.edges.append(self.edges[q].copy());self.length.append(self.length[p]+1);self.link.append(self.link[q])
                    while p>=0 and self.edges[p].get(c)==q:
                        self.edges[p][c]=clone;p=self.link[p]
                    self.link[q]=self.link[current]=clone
            last=current

    def prefix_lengths(self,text):
        # Linear storage, quadratic worst-case time; no substring table.
        result=[]
        for at in range(len(text)):
            state=0;end=at
            while end<len(text) and text[end] in self.edges[state]:
                state=self.edges[state][text[end]];end+=1
            result.append(end-at)
        return result


def suffix_array(text):
    """Prefix doubling: never construct/materialize the array of suffix strings."""
    n=len(text);order=list(range(n));ranks=list(map(ord,text));step=1
    while step<n:
        key=lambda i:(ranks[i],ranks[i+step] if i+step<n else -1)
        order.sort(key=key)
        new=[0]*n
        for a,b in zip(order,order[1:]):
            new[b]=new[a]+(key(a)!=key(b))
        ranks=new
        if ranks[order[-1]]==n-1:
            break
        step*=2
    return order


def previous_lcps(text,order):
    ranks=[0]*len(text)
    for rank,at in enumerate(order):ranks[at]=rank
    result=[0]*len(text);common=0
    for at in range(len(text)):
        rank=ranks[at]
        if not rank:
            common=0;continue
        other=order[rank-1]
        while at+common<len(text) and other+common<len(text) and text[at+common]==text[other+common]:common+=1
        result[rank]=common
        common=max(0,common-1)
    return result


def legal_guard(texts):
    compact=lambda s:''.join(s.split())
    banned=[compact(s) for s in texts]
    for text in texts:
        lines=text.splitlines(keepends=True)
        for i,line in enumerate(lines):
            if line.lstrip().startswith('def solve('):
                body=compact(''.join(lines[i+1:]))
                if body:banned.append(body)
    return lambda s:s not in texts and (len(s)==1 or not any(b in compact(s) for b in banned))


def complete_inventory(texts,deadline):
    """Two distinct source owners only. Inventory all shared strings, storing none.

    A suffix contributes only prefixes beyond its LCP with the preceding suffix;
    matching-prefix length in the other source bounds shared support exactly.
    """
    if len(texts)!=2 or any(not x for x in texts):raise ValueError('exactly two complete sources')
    legal=legal_guard(texts)
    automata=[SuffixAutomaton(s) for s in texts]
    limits=[automata[1-i].prefix_lengths(s) for i,s in enumerate(texts)]
    order=suffix_array(texts[0]);lcps=previous_lcps(texts[0],order)
    shared=allowed=0;by_length={}
    for rank,at in enumerate(order):
        if time.monotonic()>=deadline:raise TimeoutError('inventory deadline')
        for length in range(max(2,lcps[rank]+1),limits[0][at]+1):
            shared+=1
            if legal(texts[0][at:at+length]):
                allowed+=1;by_length[length]=by_length.get(length,0)+1
    alphabet=tuple(sorted(c for c in set(''.join(texts)) if legal(c)))
    return dict(shared_multichar_entries=shared,legal_shared_multichar_entries=allowed,
                excluded_multichar_entries=shared-allowed,explicit_singleton_entries=len(alphabet),
                complete_legal_entries=allowed+len(alphabet),counts_by_length=by_length,
                automaton_states=[len(a.edges) for a in automata]),limits,alphabet,legal


def relaxed_path(text,limits,legal,deadline):
    costs=[None]*(len(text)+1);costs[-1]=(0,0);choices=[None]*len(text)
    for at in range(len(text)-1,-1,-1):
        if time.monotonic()>=deadline:raise TimeoutError('relaxed DP deadline')
        best=None
        for length in range(1,max(1,limits[at])+1):
            piece=text[at:at+length]
            if not legal(piece) or costs[at+length] is None:continue
            n,c=costs[at+length]
            candidate=(n+1,c+(length==1),piece,at+length)
            if best is None or candidate<best:best=candidate
        if best is not None:
            costs[at]=best[:2];choices[at]=best[2:]
    if costs[0] is None:return None,[]
    pieces=[];at=0
    while at<len(text):
        piece,at=choices[at];pieces.append(piece)
    if ''.join(pieces)!=text:raise AssertionError('all-U witness mismatch')
    return costs[0],pieces


def residual_frontier(variants,alphabet,groups,deadline):
    """Exact subset enumeration per declared <=6-entry residual, fixed old basis.

    Coverage-preserving removal of all unused entries follows exact segmentation.
    This is NOT global dictionary optimization or complete pricing over all U.
    """
    states={capacity:None for capacity in f.PROFILES}
    ledger=[];evaluations=0
    def evaluate(dictionary):
        selected={}
        for pid,rows in sorted(variants.items()):
            paths=[(key,p) for key,text in sorted(rows.items()) if (p:=f.exact_path(text,dictionary)) is not None]
            if not paths:return None
            selected[pid]=min(paths,key=lambda x:(x[1],x[0]))
        used={i for _,path in selected.values() for i in path[2]}
        retired=tuple(s for i,s in enumerate(dictionary) if i in used)
        # Re-ID after deletion; no hidden literal renumbering channel in packets.
        chosen={pid:(key,f.exact_path(variants[pid][key],retired)) for pid,(key,_) in selected.items()}
        return retired,chosen
    for stage,group in enumerate([()]+list(groups)):
        if len(group)>6:raise ValueError('residual cap is six frozen entries')
        # Small profiles may bootstrap only from explicit charged alphabet or a
        # currently accepted larger profile; capacity is checked after retirement.
        bases={alphabet}|{row['dictionary'] for row in states.values() if row}
        candidates={}
        for basis in sorted(bases):
            for size in range(len(group)+1):
                for subset in itertools.combinations(group,size):
                    if time.monotonic()>=deadline:
                        return states,ledger,evaluations,False
                    dictionary=tuple(sorted(set(basis)|set(subset)))
                    if dictionary in candidates:continue
                    evaluated=evaluate(dictionary);evaluations+=1
                    if evaluated is not None:candidates[dictionary]=evaluated
        for dictionary,selected in candidates.values():
            for capacity in f.PROFILES:
                if len(dictionary)>capacity:continue
                row=dict(dictionary=dictionary,selected=selected,unreachable=(),
                         metrics=f.metrics(dictionary,selected,variants,capacity.bit_length()-1))
                old=states[capacity]
                objective=lambda r:(r['metrics']['selections'],r['metrics']['characters'],r['metrics']['package_bytes'],r['dictionary'])
                if old is None or objective(row)<objective(old):states[capacity]=row
                # Preserve nondominated alternatives; no cross-coverage comparison.
                previous=[x for x in ledger if x['capacity']==capacity]
                if not any(f.dominates(x['row'],row) or x['row']==row for x in previous):
                    ledger=[x for x in ledger if x['capacity']!=capacity or not f.dominates(row,x['row'])]
                    ledger.append(dict(stage=stage,capacity=capacity,row=row))
    return states,ledger,evaluations,True
