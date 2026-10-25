"""Python AST legality with the existing exact systematic composition policy."""
import ast
from collections import defaultdict
import importlib.util
from pathlib import Path
import time
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('python_incremental_bound',HERE.parent/'incremental-merge-v4/search.py');engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
joint=engine.joint;ALPHABET=engine.ALPHABET;digest=engine.digest

def forbidden(texts):
    banned=set()
    for text in texts.values():
        tree=ast.parse(text)
        banned.update((text,text.strip()))
        for node in ast.walk(tree):
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef,ast.Lambda)):
                segment=ast.get_source_segment(text,node)
                if segment:banned.update((segment,segment.strip()))
                if isinstance(node,ast.Lambda):continue
                if not node.body:raise ValueError('empty Python definition')
                first,last=node.body[0],node.body[-1]
                # AST columns are UTF8 offsets; the fixed ASCII alphabet makes
                # string/byte column indexing identical, checked before this call.
                lines=text.splitlines(keepends=True)
                start=sum(map(len,lines[:first.lineno-1]))+first.col_offset
                stop=sum(map(len,lines[:last.end_lineno-1]))+last.end_col_offset
                body=text[start:stop];banned.update((body,body.strip()))
    return {s for s in banned if s}

def family(text):
    tree=ast.parse(text);nodes=list(ast.walk(tree));attrs={n.attr for n in nodes if isinstance(n,ast.Attribute)}
    if 'next' in attrs:return 'linked-node'
    if {'left','right'} & attrs:return 'tree-node'
    loops=(ast.For,ast.While,ast.AsyncFor)
    if any(isinstance(n,loops) and any(isinstance(x,loops) for child in n.body for x in ast.walk(child)) for n in nodes) and any(isinstance(n,ast.Subscript) for n in nodes):return 'indexed-nesting'
    if any(isinstance(n,(ast.Dict,ast.Set,ast.DictComp,ast.SetComp)) or isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in ('dict','set') for n in nodes):return 'map-set'
    if any(isinstance(n,loops) for n in nodes):return 'sequence-loop'
    if any(isinstance(n,ast.BinOp) for n in nodes):return 'arithmetic-recursion'
    return 'other'

class Builder(engine.Builder):
    """Reuse scoring/moves/bounds, not JavaScript-specific parser or source gate."""
    def __init__(self,texts,owners,references,families,*,capacity,record=None,resume=(),cpu_seconds=None,initial=(),audited_helpers=()):
        if audited_helpers:raise ValueError('Python whole helpers require a separate audit; none approved')
        if capacity not in (128,256):raise ValueError('unsupported capacity')
        if set(texts)!=set(owners) or set(references)!=set(owners.values()) or set(families)!=set(references):raise ValueError('incomplete source population')
        if any(references[p] not in texts or owners[references[p]]!=p for p in references):raise ValueError('invalid source reference')
        joint.compare.validate_texts(texts)
        self.texts,self.owners,self.references,self.families=texts,owners,references,families
        self.capacity=capacity;self.graph=joint.compact.Graph(texts);self.graphs={};self.legal_cache={}
        self.banned=forbidden(texts);self.hard_banned=self.banned.copy();self.allowed={};self.initial=list(initial)
        self.groups=defaultdict(list)
        for key,pid in sorted(owners.items()):self.groups[pid].append(key)
        self.record=record or (lambda row:None);self.chain='0'*64;self.events=[];self.frontiers=defaultdict(list);self.evaluations=0
        self.deadline=None if cpu_seconds is None else time.process_time()+cpu_seconds
        self.resumed={}
        for row in resume:
            saved=dict(row);expected=saved.pop('sha256')
            if saved['previous_sha256']!=self.chain or digest(saved)!=expected:raise ValueError('growth ledger chain mismatch')
            self.chain=expected;self.evaluations=row['evaluations']
            for suffix in ('-start','-add','-exhausted'):
                if row['operation'].endswith(suffix):self.resumed[(row['operation'][:-len(suffix)],tuple(row['ids']))]=row;break
            self.frontiers[tuple(row['ids'])]=row['frontier']

    def family_growth(self):
        """The original deterministic local growth/overlap-merging hierarchy."""
        return engine.search.v2.legacy.Builder.run(self)
