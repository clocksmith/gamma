"""Original Hack2Hire 68504f81839fbdf76404b1d1 native class variant over an INFERRED specification, with a separately declared trace adapter; qualification unknown."""

LIVE = float('inf')


class SnapshotSet:
    def __init__(self):
        self.entries = []   # [value, removed_at_version]
        self.position = {}  # live value -> entry index
        self.version = 0
        self.iterators = []  # [version, end, cursor]

    def add(self, value):
        if value in self.position:
            return False
        self.version += 1
        self.position[value] = len(self.entries)
        self.entries.append([value, LIVE])
        return True

    def remove(self, value):
        if value not in self.position:
            return False
        self.version += 1
        self.entries[self.position.pop(value)][1] = self.version
        return True

    def contains(self, value):
        return value in self.position

    def getIterator(self):
        self.iterators.append([self.version, len(self.entries), 0])
        return len(self.iterators) - 1

    def hasNext(self, iteratorId):
        it = self.iterators[iteratorId]
        while it[2] < it[1] and self.entries[it[2]][1] <= it[0]:
            it[2] += 1
        return it[2] < it[1]

    def next(self, iteratorId):
        if not self.hasNext(iteratorId):
            raise IndexError('iterator exhausted')
        it = self.iterators[iteratorId]
        it[2] += 1
        return self.entries[it[2] - 1][0]


def solve(operation_names, argument_lists):
    if operation_names[0] != 'SnapshotSet' or argument_lists[0] != []:
        raise ValueError('exact initial constructor required')
    instance, result = SnapshotSet(), [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in ('add', 'remove', 'contains', 'getIterator', 'hasNext', 'next'):
            raise ValueError('unknown method')
        result.append(getattr(instance, name)(*arguments))
    return result
