"""Hack2Hire 6920d4a994b324049c3251c1 (Design KV Store with Rollback, variant 3 of 3) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class KeyValueStore:
    def __init__(self):
        self.data = {}
        self.logs = []  # one undo log (key -> old value or None) per open transaction
        self.counts = {}  # value -> number of keys holding it

    def set(self, key, value):
        self._assign(key, value)

    def get(self, key):
        return self.data.get(key, '')

    def unset(self, key):
        self._assign(key, None)

    def _apply(self, key, value):
        old = self.data.get(key)
        if old is not None:
            self.counts[old] -= 1
        if value is not None:
            self.counts[value] = self.counts.get(value, 0) + 1
        if value is None:
            self.data.pop(key, None)
        else:
            self.data[key] = value

    def _assign(self, key, value):
        if self.logs and key not in self.logs[-1]:
            self.logs[-1][key] = self.data.get(key)  # first change in this transaction: remember the old value
        self._apply(key, value)

    def begin(self):
        self.logs.append({})

    def rollback(self):
        if not self.logs:
            return False
        for key, old in self.logs.pop().items():
            self._apply(key, old)
        return True

    def commit(self):
        if not self.logs:
            return False
        self.logs = []
        return True

    def count(self, value):
        return self.counts.get(value, 0)


def solve(operation_names, argument_lists):
    if operation_names[0] != 'KeyValueStore' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = KeyValueStore(*argument_lists[0])
    allowed = {'set', 'get', 'unset', 'begin', 'rollback', 'commit', 'count'}
    voids = {'set', 'unset', 'begin'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
