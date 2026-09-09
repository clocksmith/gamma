"""Replace one literal context with causal completed-word history."""
import hashlib
import types

PARENT_SHA = '7d331ba82c635af8afe6517bf5f4471b41dcf7854c6ec01cb5564078d9bb56a8'


def install(ns, packed_parent, arm):
    if arm not in ('P', 'K', 'D', 'S'):
        raise ValueError('unknown previous-word arm')
    if hashlib.sha256(packed_parent).hexdigest() != PARENT_SHA:
        raise ValueError('parent identity differs')
    if arm == 'P':
        return ns
    BaseGST, BaseLIT = ns['GST'], ns['LIT']
    # Copy before replacing either class: parse costs use the original models.
    parent_prefix = types.FunctionType(ns['lit_prefix'].__code__, dict(ns))

    class State(BaseGST):
        def __init__(self):
            super().__init__()
            self._completed_words = (b'', b'')

        def completed_words(self):
            return self._completed_words

        def up(self, byte):
            completed = (bytes(self.word[-8:]) if self.word and
                         not (65 <= byte <= 90 or 97 <= byte <= 122) else b'')
            super().up(byte)
            if completed:
                self._completed_words = (completed, self._completed_words[0])

    class Literal(BaseLIT):
        def keys(self, state, prefix):
            keys = super().keys(state, prefix)
            if len(keys) != 12:
                raise ValueError('literal family count differs')
            previous = state.completed_words()[0 if arm == 'D' else 1]
            return keys[:11] + ((prefix, previous, bytes(state.word[-2:]), state.f),)

    ns.update(GST=State, LIT=BaseLIT if arm == 'K' else Literal,
              _previous_word_parent_prefix=parent_prefix)
    exec('def lit_prefix(data):\n return _previous_word_parent_prefix(data)\n', ns)
    return ns
