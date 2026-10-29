"""Hack2Hire 67a19e53b41c4108d8ccb3d4 (Design In-Memory Key-Value Database, variant 1) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

_ABSENT = object()


class InMemoryKVDB:
    def __init__(self):
        self._data = {}
        self._counts = {}
        self._undo = []  # one dict per open transaction: key -> value before the transaction touched it

    def _write(self, key, value):
        if self._undo and key not in self._undo[-1]:
            self._undo[-1][key] = self._data.get(key, _ABSENT)
        old = self._data.get(key, _ABSENT)
        if old is not _ABSENT:
            self._counts[old] -= 1
            del self._data[key]
        if value is not _ABSENT:
            self._data[key] = value
            self._counts[value] = self._counts.get(value, 0) + 1

    def set(self, key, value):
        self._write(key, value)

    def get(self, key):
        return self._data.get(key)

    def delete(self, key):
        if key in self._data:
            self._write(key, _ABSENT)

    def count(self, value):
        return self._counts.get(value, 0)

    def begin(self):
        self._undo.append({})

    def rollback(self):
        if not self._undo:
            return False
        log = self._undo.pop()
        saved, self._undo = self._undo, []
        for key, value in log.items():
            self._write(key, value)
        self._undo = saved
        return True

    def commit(self):
        if not self._undo:
            return False
        self._undo = []
        return True


def solve(operation_names, argument_lists):
    if operation_names[0] != 'InMemoryKVDB':
        raise ValueError('exact initial constructor required')
    instance = InMemoryKVDB(*argument_lists[0])
    allowed = ['set', 'get', 'delete', 'count', 'begin', 'rollback', 'commit']
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        result.append(getattr(instance, name)(*arguments))
    return result
