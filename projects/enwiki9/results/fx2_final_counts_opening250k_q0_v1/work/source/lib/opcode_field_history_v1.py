"""Persistent decoder-built body suffixes; original codec laws remain external."""


def install(ns, arm):
    if arm not in ('P', 'K', 'D', 'G', 'S'):
        raise ValueError('unknown history arm')
    if arm == 'P':
        return ns
    BaseState, BaseLiteral = ns['GST'], ns['LIT']
    openings = (15, 17, 9, 11, 13, 1)

    class State(BaseState):
        def __init__(self):
            super().__init__()
            self.histories = [b''] * 7
            self.route = -1
            self.rng = 2463534242
            self.entries = self.body_bytes = 0

        def up(self, byte):
            pending, field = self.field.pending, self.f
            literal = 0 if pending and byte == 255 else byte if not pending and byte else None
            super().up(byte)
            if field and literal is not None:
                if not 0 <= self.route < 7:
                    raise ValueError('body byte without a decoded route')
                self.histories[self.route] = (self.histories[self.route] + bytes((literal,)))[-3:]
                self.body_bytes += 1
            if pending and byte in openings:
                self.entries += 1
                if arm == 'S':
                    x = self.rng
                    x ^= (x << 13) & 0xffffffff
                    x ^= x >> 17
                    x ^= (x << 5) & 0xffffffff
                    self.rng = x
                    self.route = 1 + x % 6
                else:
                    self.route = 0 if arm == 'G' else self.f
            elif not self.f:
                self.route = -1

    class Literal(BaseLiteral):
        def keys(self, state, prefix):
            original = super().keys(state, prefix)
            if not state.f or state.field.pending:
                return original
            history = state.histories[state.route]
            proposed = ((prefix, state.f, history[-2:]), (prefix, state.f, history))
            return original if arm == 'K' else original[:8] + proposed + original[10:]

    ns['GST'], ns['LIT'] = State, Literal
    return ns


def side_state(state):
    if not hasattr(state, 'histories'):
        return None
    return (tuple(state.histories), state.route, state.rng, state.entries, state.body_bytes)
