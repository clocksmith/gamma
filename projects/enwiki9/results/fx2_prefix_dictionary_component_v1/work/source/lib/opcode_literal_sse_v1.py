"""Calibrate on coded literals; preserve all-byte counts, weights and parse costs."""
import hashlib
import types

PARENT_SHA = '7d331ba82c635af8afe6517bf5f4471b41dcf7854c6ec01cb5564078d9bb56a8'


def install(ns, packed_parent, arm):
    if arm not in ('P', 'K', 'D'):
        raise ValueError('unknown literal SSE arm')
    if hashlib.sha256(packed_parent).hexdigest() != PARENT_SHA:
        raise ValueError('parent identity differs')
    if arm == 'P':
        return ns
    BaseLIT = ns['LIT']
    # Freeze the original all-byte estimator and therefore the original parse.
    # Its class methods retain the original namespace's output bound.
    parent_prefix = types.FunctionType(ns['lit_prefix'].__code__, dict(ns))

    class Literal(BaseLIT):
        def __init__(self):
            super().__init__()
            self.in_literal = False
            self.copied_bit_updates = 0

        def enc(self, coder, state, byte):
            if self.in_literal:
                raise ValueError('nested literal mode')
            self.in_literal = True
            try:
                return super().enc(coder, state, byte)
            finally:
                self.in_literal = False

        def dec(self, coder, state):
            if self.in_literal:
                raise ValueError('nested literal mode')
            self.in_literal = True
            try:
                return super().dec(coder, state)
            finally:
                self.in_literal = False

        def update(self, keys, bucket, mixed, stretches, weights, bit):
            previous = self.sse.get(bucket)
            saved = None if previous is None else tuple(previous)
            super().update(keys, bucket, mixed, stretches, weights, bit)
            if not self.in_literal:
                self.copied_bit_updates += 1
                if arm == 'D':
                    # Undo only SSE training. Context counts and SGD weights
                    # retain the parent's update on every reconstructed bit.
                    if saved is None:
                        del self.sse[bucket]
                    else:
                        previous[:] = saved
                        self.sse[bucket] = previous

    ns.update(LIT=Literal, _literal_sse_parent_prefix=parent_prefix)
    exec('def lit_prefix(data):\n return _literal_sse_parent_prefix(data)\n', ns)
    return ns
