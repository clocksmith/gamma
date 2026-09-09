"""Preserve predecessor witnesses and check the compact tracking sentinel."""
from opcode_previous_word_observe_v1 import observe as word_observe


def observe(ns, arm):
    if arm not in ('P', 'K', 'D', 'S') or ns.get('_arm') != arm:
        raise ValueError('compact arm differs')
    Base = ns['GST']

    class State(Base):
        def completed_words(self):
            # The unobserved prefix estimator deliberately uses None. Actual
            # K/D/S stream states must track; actual P states must not track.
            # Otherwise None and the empty word pair would hash identically
            # despite having different future key/update behavior.
            if (self._completed_words is None) != (arm == 'P'):
                raise ValueError('compact stream tracking state differs')
            return super().completed_words()

    ns['GST'] = State
    return word_observe(ns, arm)


def execute(module, operation, data, arm, observed=True):
    if operation not in ('encode', 'decode'):
        raise ValueError('unknown operation')
    ns = module.namespace(arm)
    captured = observe(ns, arm) if observed else None
    out = ns['compress' if operation == 'encode' else 'decompress'](data)
    return out, captured['audit'] if observed else None
