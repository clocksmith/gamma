"""Indexed cross-owner long spans and source-complementary bounded bundles.

This proposes exact strings, not macros; the scoring caller charges each entry.
"""
import itertools
import time
import frontier as f
from repeated import suffix_array,previous_lcps


def longest_cross_owner(texts):
    """Generalized suffix array; nearest different-owner suffix on each side.

    Storage is linear in input codepoints. Unique separators cannot leak into spans.
    Returns max matching prefix length per position, with a distinct-owner witness.
    """
    owners=sorted(texts);parts=[];labels=[];offsets={};used=set(''.join(texts.values()))
    for i,pid in enumerate(owners):
        separator=chr(0xE000+i)
        if separator in used:raise ValueError('synthetic index separator collision')
        offsets[pid]=len(labels);parts.append(texts[pid]+separator)
        labels.extend([pid]*len(texts[pid])+[None])
    joined=''.join(parts);order=suffix_array(joined);lcps=previous_lcps(joined,order)
    result=[0]*len(joined);bound=0
    for rank in range(1,len(order)):
        at,previous=order[rank],order[rank-1]
        bound=lcps[rank] if labels[at]!=labels[previous] else min(bound,lcps[rank])
        result[at]=max(result[at],bound)
    bound=0
    for rank in range(len(order)-2,-1,-1):
        at,following=order[rank],order[rank+1]
        bound=lcps[rank+1] if labels[at]!=labels[following] else min(bound,lcps[rank+1])
        result[at]=max(result[at],bound)
    return {pid:result[offsets[pid]:offsets[pid]+len(texts[pid])] for pid in owners}


def complementary_worklist(texts,basis,helper,legal,baseline_costs,deadline,min_length=16):
    """All bounded subsets of each source's indexed relaxed-path complements.

    Long spans are left-maximal cross-owner matches, length>=16; not a complete U.
    Every path supplies a finite required-entry set. Each bundle contains the exact
    reviewed helper plus up to4 required long spans, fitting the251-entry anchor.
    No frequency/top-K selector. A target must become strictly cheaper than its
    current selected source before its bundle is globally priced. This is a declared
    source-switch experiment, not global optimization of all literal candidates.
    """
    limits=longest_cross_owner(texts);pieces=set();witnesses={};stored_bytes=0
    for pid,text in sorted(texts.items()):
        for at,length in enumerate(limits[pid]):
            if time.monotonic()>=deadline:raise TimeoutError('long-span index budget')
            if length<min_length or at and limits[pid][at-1]>=length+1:continue
            piece=text[at:at+length]
            if piece==helper or helper in piece or not legal(piece):continue
            if piece not in pieces:
                stored_bytes+=len(piece.encode())
                if stored_bytes>1024**2:raise ValueError('long-span materialization budget; no silent truncation')
                pieces.add(piece)
            witnesses.setdefault(piece,set()).add(pid)
    # Index matched other owners, but the identical maximal occurrence need not
    # be left-maximal there. Verify actual distinct-source support independently.
    pieces=sorted(p for p in pieces if sum(p in t for t in texts.values())>=2)
    relaxed=tuple(basis)+tuple(p for p in [helper,*pieces] if p not in basis)
    work={};diagnostics={};tested=0;rejected=0;overflow=0
    for pid,text in sorted(texts.items(),key=lambda x:int(x[0]) if x[0].isdigit() else x[0]):
        path=f.exact_path(text,relaxed)
        if path is None:
            diagnostics[pid]={'relaxed_reachable':False};continue
        needed=sorted({relaxed[i] for i in path[2]}-set(basis)-{helper})
        diagnostics[pid]=dict(relaxed_reachable=True,relaxed_selections=path[0],relaxed_characters=path[1],
            long_complements=len(needed),incumbent_selections=baseline_costs[pid][0],incumbent_characters=baseline_costs[pid][1])
        for size in range(min(4,len(needed))+1):
            for subset in itertools.combinations(needed,size):
                if time.monotonic()>=deadline:raise TimeoutError('complementary bundle freeze budget')
                bundle=tuple(dict.fromkeys((helper,*subset)))
                vocab=tuple(basis)+tuple(p for p in bundle if p not in basis)
                if len(vocab)>256:overflow+=1;continue
                tested+=1;trial=f.exact_path(text,vocab)
                if trial is None or trial[:2]>=baseline_costs[pid]:rejected+=1;continue
                work.setdefault(bundle,set()).add(pid)
    # Prioritize the coherent most-complementary bundles, then exact content order;
    # all remain in the frozen worklist, and budget truncation remains explicit.
    bundles=sorted(work,key=lambda b:(-len(b),b))
    summary=dict(indexed_sources=len(texts),min_long_span_codepoints=min_length,
        unique_legal_maximal_long_spans=len(pieces),materialized_fragment_bytes=stored_bytes,
        target_subset_trials=tested,target_noncompetitive_rejections=rejected,capacity_rejections=overflow,
        bundles=len(bundles),target_diagnostics=diagnostics,
        declared_scope='Source-competitive subsets of indexed maximal-span relaxed paths, <=4 long spans plus reviewed helper; not complete U/pricing/global optimality',
        ordering='descending complementary bundle cardinality, then exact literal order; no top-K discard')
    return bundles,summary,{f.base.digest(str(b).encode()):sorted(work[b]) for b in bundles}


def pair_frontier_repairs(anchor, repairs, unlocking_bundles, capacity=256):
    """Exact frozen cross-product, no assumption that costs add independently.

    Prior character-saving dictionaries retain their identity; over-capacity unions
    remain explicit proposals requiring retirement before legal scoring. No protected sources, renaming or free IDs.
    """
    proposals=set();overflow=0
    for repair in repairs:
        additions=tuple(p for p in repair if p not in anchor)
        for bundle in unlocking_bundles:
            combined=tuple(dict.fromkeys((*additions,*bundle)))
            if len(set(anchor)|set(combined))>capacity:
                overflow+=1
            proposals.add(combined)
    return sorted(proposals,key=lambda b:(len(set(anchor)|set(b))>capacity,-len(b),b)),overflow


def clean_union(vocabulary,texts,owners,references,deadline):
    """Capacity-relaxed exact DP solely to identify coverage-preserving unused retirement.

    Never report the overcomplete dictionary as feasible. Re-evaluate every source
    variant; then remove entries absent from all selected paths. If still over cap,
    caller must enumerate explicit active-entry deletions or report pending work.
    """
    selected={}
    for key,text in sorted(texts.items()):
        if time.monotonic()>=deadline:raise TimeoutError('union retirement pricing deadline')
        try:ids=f.seg.shortest_encode(text,list(vocabulary))
        except ValueError as exc:
            if str(exc)=='source cannot be represented':continue
            raise
        pid=owners[key]
        rank=(len(ids),sum(len(vocabulary[i])==1 for i in ids),key!=references[pid],key)
        if pid not in selected or rank<selected[pid][0]:selected[pid]=(rank,ids)
    if set(selected)!=set(references):return None
    used={i for _,ids in selected.values() for i in ids}
    return tuple(piece for i,piece in enumerate(vocabulary) if i in used)
