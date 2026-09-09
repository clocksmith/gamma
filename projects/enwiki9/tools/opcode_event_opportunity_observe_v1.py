"""Observe actual compact-parent token events without changing codec state.

Records are diagnostics, not probabilities supplied to the decoder. Callers own
the record sink and execution bounds; this module creates no files or jobs.
"""
import hashlib
import lzma
from weakref import WeakKeyDictionary

from tools.opcode_field_compact_observe_v1 import observe
from tools.opcode_field_repair_cli_v1 import Audit


PARENT_SHA256 = '7d331ba82c635af8afe6517bf5f4471b41dcf7854c6ec01cb5564078d9bb56a8'


def namespace(packed_parent):
    """Authenticate the immutable source before decompression or execution."""
    if hashlib.sha256(packed_parent).hexdigest() != PARENT_SHA256:
        raise ValueError('compact event observer parent differs')
    ns = {'__name__': 'opcode_event_opportunity_parent'}
    exec(compile(lzma.decompress(packed_parent), '<compact-parent>', 'exec'), ns)
    return ns


def observe_events(ns, emit, *, max_events):
    """Wrap authenticated TOK; side state belongs to this external observer.

    Install after the existing common observer. Neither snapshots nor emission
    call ev(), m(), cf(), find() or up(); only real eve/evd calls emit records.
    The limit counts all emitted events, including across multiple TOK objects.
    """
    if type(max_events) is not int or max_events < 0 or not callable(emit):
        raise ValueError('invalid event observation bound or sink')
    base = ns['TOK']
    histories = WeakKeyDictionary()
    emitted = 0

    def before(tokens, state):
        if emitted >= max_events:
            raise ValueError('event observation bound exceeded')
        key = (state.f, state.w, state.pg, state.c)
        model = tokens.e.get(key)
        counts, total = ((1, 1, 1), 3) if model is None else (tuple(model.c), model.t)
        index, previous = histories.get(tokens, (0, None))
        return dict(index=index, position=state.position, key=key,
                    previous_event=previous, pre_counts=counts, pre_total=total)

    def after(tokens, record, event):
        nonlocal emitted
        model = tokens.e[record['key']]
        record.update(event=event, post_counts=tuple(model.c), post_total=model.t)
        emit(record)
        histories[tokens] = (record['index'] + 1, event)
        emitted += 1

    class Tokens(base):
        def eve(self, coder, state, event):
            record = before(self, state)
            result = super().eve(coder, state, event)
            after(self, record, event)
            return result

        def evd(self, coder, state):
            record = before(self, state)
            event = super().evd(coder, state)
            after(self, record, event)
            return event

    ns['TOK'] = Tokens


def execute(packed_parent, operation, data, *, emit=None, max_events=0):
    """Run the exact parent with common audits and optional bounded event records.

    emit=None is P; supplying an external sink is bookkeeping-only K. The caller
    must separately authorize and bound any execution on a measured population.
    """
    if operation not in ('encode', 'decode'):
        raise ValueError('unknown compact event observer operation')
    ns = namespace(packed_parent)
    captured = observe(ns, Audit('D'))
    if emit is not None:
        observe_events(ns, emit, max_events=max_events)
    output = ns['compress' if operation == 'encode' else 'decompress'](data)
    return output, captured['audit']
