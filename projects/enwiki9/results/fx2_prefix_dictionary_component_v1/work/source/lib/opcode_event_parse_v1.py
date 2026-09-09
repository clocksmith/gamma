"""Encoder-only adaptive event pricing over the authenticated compact parent."""
import hashlib

from lib.opcode_literal_event_cost_v1 import literal_event_costs

PARENT_SHA = '7d331ba82c635af8afe6517bf5f4471b41dcf7854c6ec01cb5564078d9bb56a8'


def event_keys(state_type, data):
    """Pre-byte contexts: GST advances on all bytes, regardless of parse mode."""
    state, keys = state_type(), []
    for byte in data:
        keys.append((state.f, state.w, state.pg, state.c))
        state.up(byte)
    return keys


def install(ns, packed_parent, arm):
    if arm not in ('P', 'K', 'D'):
        raise ValueError('unknown event pricing arm')
    if hashlib.sha256(packed_parent).hexdigest() != PARENT_SHA:
        raise ValueError('event pricing parent differs')
    if arm == 'P':
        return ns
    import lzma
    source = lzma.decompress(packed_parent).decode()
    start = source.index('def compress_inner(d):')
    end = source.index('def decompress_inner', start)
    body = source[start:end]
    substitutions = (
        (' cnt=[0,0,0];mb=[0,0,0]',
         ' event_contexts=_event_keys(d)\n cnt=[0,0,0];mb=[0,0,0]'),
        ('   for L,D in rawm(d,i,ht):',
         '   raw_candidates=rawm(d,i,ht)\n'
         '   chain_candidates=chainm(d,i,ch,st)\n'
         '   span=max((v[0] for v in raw_candidates+chain_candidates),default=0)\n'
         '   event_costs,_=_literal_event_costs(tok.e,event_contexts[i:i+span])\n'
         '   for L,D in raw_candidates:'),
        ('   for L,lev,idx,j in chainm(d,i,ch,st):',
         '   for L,lev,idx,j in chain_candidates:'),
    )
    for old, new in substitutions:
        if body.count(old) != 1:
            raise ValueError('parent encoder structure differs')
        body = body.replace(old, new)
    old = 'L*tok.evc(st,0)'
    if body.count(old) != 2:
        raise ValueError('parent literal cost sites differ')
    body = body.replace(old, "(event_costs[L] if _event_cost_arm=='D' else L*tok.evc(st,0))")
    base_state = ns['GST']
    ns.update(_event_cost_arm=arm, _literal_event_costs=literal_event_costs,
              _event_keys=lambda data: event_keys(base_state, data))
    exec(compile(body, '<opcode-event-parse-v1>', 'exec'), ns)
    return ns
