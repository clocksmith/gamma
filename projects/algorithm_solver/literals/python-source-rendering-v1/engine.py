"""Pure supplied-text U/S/D/J experiment adapter; no population or case loader."""
import copy
import importlib.util
import os
import sys
from pathlib import Path
import render

if not __debug__ or 'PYTHONOPTIMIZE' in os.environ:
    raise RuntimeError('Normal Python assertion checks are required')
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('python_renderer_parent_backend',HERE.parent/'python-binding-continuation-v1/backend.py')
parent=importlib.util.module_from_spec(spec)
_search_path=list(sys.path)
try:spec.loader.exec_module(parent)
finally:sys.path[:]=_search_path
ARMS=('U','S','D','J')


def normalized(original,choices):
    """Frozen evaluator's (N, bytes, variant ID) tie becomes unchanged-first."""
    others=sorted(set(choices)-{original})
    return {'v000_original':original,**{f'v{i:03d}':text for i,text in enumerate(others,1)}}


def source_menus(texts):
    menus={pid:render.menu(text) for pid,text in sorted(texts.items())}
    groups={pid:normalized(texts[pid],menu['candidates'].values()) for pid,menu in menus.items()}
    return groups,menus


def choose(texts,groups,vocab,width):
    """Canonical N, full packet bytes, source bytes, unchanged, then source text."""
    assert set(texts)==set(groups) and width in (7,8) and len(vocab)<=2**width
    chosen,trace={},{}
    for pid,variants in sorted(groups.items()):
        assert texts[pid] in variants.values()
        scored=[]
        for text in variants.values():
            render.validate(texts[pid],text)
            seq=parent.analyze.shortest_encode(text,vocab)
            packet=parent.analyze.encode(vocab,seq,width)
            assert parent.analyze.decode(parent.analyze.dictionary_bytes(vocab),packet)==text
            score=(len(seq),len(packet),len(text.encode()),text!=texts[pid],text)
            scored.append((score,text))
        score,text=min(scored)
        chosen[pid]=text
        trace[pid]={'variants':len(variants),'selections':score[0],'packet_bytes':score[1],
                    'source_bytes':score[2],'unchanged':text==texts[pid],
                    'source_sha256':parent.analyze.sha(text.encode())}
    return chosen,trace


def polish(variants,vocab,width,ban,cfg,enabled):
    """Frozen search primitives with the same all-menu exclusion in D and J."""
    budget=parent.v3.Budget(cfg['search'])
    state=parent.v3.evaluate(variants,vocab,width,None,budget);log=[];stop='fixed_dictionary'
    if enabled:
        proposer=parent.style.hybrid_chosen([],variants)
        def safe(s,st,limit,fraction):
            return [p for p in proposer(s,st,limit,fraction) if p not in ban]
        state,_=parent.v3.refill(variants,state,width,safe,cfg['neighborhood'],24,budget)
        state,stop=parent.v3.local_search(variants,state,width,safe,cfg['neighborhood'],budget,log)
    assert budget.trials<=cfg['search']['trials']
    return state,{'trials':budget.trials,'stop':stop,'seconds':budget.elapsed(),
                  'selections':state['selections'],'trace':log}


def fit_arm_supplied(texts,seed,width,entries,cfg,arm):
    """Fit-only API. Caller owns cohort authority, process limits and sealing."""
    assert width in (7,8) and set(texts)==set(entries)
    assert len(seed)<=2**width and set(render.ALPHABET)<=set(seed)
    assert seed==parent.v3.joint.order(seed),'seed must already have canonical dictionary order'
    groups,menus=source_menus(texts)
    fixed={pid:normalized(text,[text]) for pid,text in texts.items()}
    assert arm in ARMS
    ban=parent.banned(groups,entries)
    variants=groups if arm in ('S','J') else fixed
    vocab=list(seed);history=[]
    for _ in range(cfg['rounds'] if arm in ('D','J') else 1):
        state,info=polish(variants,vocab,width,ban,cfg,arm in ('D','J'))
        vocab=state['vocab'];history.append(info)
    if arm in ('U','S'):assert vocab==seed,'fixed dictionary changed'
    selected,trace=choose(texts,variants,vocab,width)
    assert selected=={pid:variants[pid][label] for pid,label in state['chosen'].items()}
    assert state['selections']==sum(row['selections'] for row in trace.values())
    return {'arm':arm,'dictionary':vocab,'fit_sources':selected,'variants':copy.deepcopy(variants),
            'fit_selections':state['selections'],'source_choices':trace,'search':history,'menus':menus,
            'all_menu_bans':sorted(ban),
            'validation_loaded':False,'case_data_loaded':False}


def fit_supplied(texts,seed,width,entries,cfg):
    results={arm:fit_arm_supplied(texts,seed,width,entries,cfg,arm) for arm in ARMS}
    return {'arms':results,'menus':results['U']['menus'],'all_menu_bans':results['U']['all_menu_bans'],
            'validation_loaded':False,'case_data_loaded':False}


def validation_supplied(texts,sealed,width):
    """Same deterministic menu, no dictionary fit, no cases or verdict input."""
    assert set(sealed)==set(ARMS)
    groups,menus=source_menus(texts)
    fixed={pid:normalized(text,[text]) for pid,text in texts.items()}
    result={}
    for arm in ARMS:
        variants=groups if arm in ('S','J') else fixed
        sources,trace=choose(texts,variants,sealed[arm],width)
        result[arm]={'sources':sources,'variants':copy.deepcopy(variants),'source_choices':trace}
    return result,menus
