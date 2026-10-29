"""Hack2Hire 689e4cd9735253d430dee92f (Cloud Storage System, variant 4) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

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

    def findFile(self, prefix, suffix):
        if self._names_stale:
            self._names = sorted(self._files)
            self._names_stale = False
        hits = []
        for i in range(bisect_left(self._names, prefix), len(self._names)):
            name = self._names[i]
            if not name.startswith(prefix):
                break
            if name.endswith(suffix):
                hits.append((-self._files[name][0], name))
        hits.sort()
        return [name + '(' + str(-negative) + ')' for negative, name in hits]

    def addUser(self, userId, capacity):
        if userId in self._capacity:
            return False
        self._capacity[userId] = capacity
        self._used[userId] = 0
        self._owned[userId] = set()
        return True

    def addFileBy(self, userId, name, size):
        if userId not in self._capacity or name in self._files or self._used[userId] + size > self._capacity[userId]:
            return -1
        self._store(name, size, userId)
        self._used[userId] += size
        self._owned[userId].add(name)
        return self._capacity[userId] - self._used[userId]

    def mergeUser(self, userId1, userId2):
        if userId1 == userId2 or userId1 not in self._capacity or userId2 not in self._capacity:
            return -1
        for name in self._owned[userId2]:
            self._files[name] = (self._files[name][0], userId1)
        self._owned[userId1] |= self._owned.pop(userId2)
        self._used[userId1] += self._used.pop(userId2)
        self._capacity[userId1] += self._capacity.pop(userId2)
        self._backups.pop(userId2, None)
        return self._capacity[userId1] - self._used[userId1]

    def backupUser(self, userId):
        if userId not in self._capacity:
            return -1
        self._backups[userId] = [(name, self._files[name][0]) for name in self._owned[userId]]
        return len(self._backups[userId])

    def restoreUser(self, userId):
        if userId not in self._capacity:
            return -1
        for name in self._owned[userId]:
            del self._files[name]
        self._names_stale = True
        self._owned[userId] = set()
        self._used[userId] = 0
        restored = 0
        for name, size in self._backups.get(userId, []):
            if name not in self._files:
                self._store(name, size, userId)
                self._owned[userId].add(name)
                self._used[userId] += size
                restored += 1
        return restored


def solve(operation_names, argument_lists):
    if operation_names[0] != 'CloudStorage':
        raise ValueError('exact initial constructor required')
    instance = CloudStorage(*argument_lists[0])
    allowed = ['addFile', 'copyFile', 'getFilesize', 'findFile', 'addUser', 'addFileBy', 'mergeUser', 'backupUser', 'restoreUser']
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        result.append(getattr(instance, name)(*arguments))
    return result
