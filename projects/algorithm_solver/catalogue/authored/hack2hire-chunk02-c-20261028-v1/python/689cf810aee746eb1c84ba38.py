"""Hack2Hire 689cf810aee746eb1c84ba38 (Cloud Storage System, variant 1) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

from bisect import bisect_left, insort


class CloudStorage:
    def __init__(self):
        self._files = {}  # name -> (size, owner); owner None = unlimited admin
        self._names = []  # sorted file names, rebuilt lazily when _names_stale
        self._names_stale = False
        self._capacity = {}
        self._used = {}
        self._owned = {}
        self._backups = {}

    def addFile(self, name, size):
        if name in self._files:
            return False
        self._store(name, size, None)
        return True

    def _store(self, name, size, owner):
        self._files[name] = (size, owner)
        if not self._names_stale:
            insort(self._names, name)

    def copyFile(self, nameFrom, nameTo):
        source = self._files.get(nameFrom)
        if source is None or nameTo in self._files:
            return False
        size, owner = source
        if owner is not None:
            if self._used[owner] + size > self._capacity[owner]:
                return False
            self._used[owner] += size
            self._owned[owner].add(nameTo)
        self._store(nameTo, size, owner)
        return True

    def getFilesize(self, name):
        entry = self._files.get(name)
        return -1 if entry is None else entry[0]


def solve(operation_names, argument_lists):
    if operation_names[0] != 'CloudStorage':
        raise ValueError('exact initial constructor required')
    instance = CloudStorage(*argument_lists[0])
    allowed = ['addFile', 'copyFile', 'getFilesize']
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        result.append(getattr(instance, name)(*arguments))
    return result
