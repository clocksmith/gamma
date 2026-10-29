"""Hack2Hire 69d16c5617b72775cc49bf93 (Design Document Layer System, variant 1) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

_ABSENT = object()


class Document:
    def __init__(self):
        self.layers = {}
        self.undo_stack = []  # (layer, key, before, after)

    def _put(self, layerId, key, value):
        layer = self.layers.setdefault(layerId, {})
        if value is _ABSENT:
            del layer[key]
        else:
            layer[key] = value

    def _change(self, layerId, key, after):
        before = self.layers.get(layerId, {}).get(key, _ABSENT)
        self._put(layerId, key, after)
        self.undo_stack.append((layerId, key, before, after))

    def setProperty(self, layerId, key, value):
        self._change(layerId, key, value)

    def getProperty(self, layerId, key):
        return self.layers.get(layerId, {}).get(key)

    def undo(self):
        if not self.undo_stack:
            return False
        entry = self.undo_stack.pop()
        self._put(entry[0], entry[1], entry[2])
        return True


def solve(operation_names, argument_lists):
    if operation_names[0] != 'Document' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = Document()
    allowed = ['setProperty', 'getProperty', 'undo']
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        result.append(getattr(instance, name)(*arguments))
    return result
