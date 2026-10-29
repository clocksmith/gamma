"""Hack2Hire 68dd9212fb98b196fa540558 (Flatten 2D Array With Remove) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class Vector2D:
    def __init__(self, vec):
        self.rows = [list(row) for row in vec]
        self.dead = [[False] * len(row) for row in vec]  # lazy removal flags
        self.removed = [0] * len(vec)
        self.r = 0
        self.c = 0
        self.last = None

    def _skip(self):
        rows = self.rows
        while self.r < len(rows) and self.c >= len(rows[self.r]):
            self.r += 1
            self.c = 0

    def next(self):
        self._skip()
        value = self.rows[self.r][self.c]
        self.last = (self.r, self.c)
        self.c += 1
        return value

    def hasNext(self):
        self._skip()
        return self.r < len(self.rows)

    def remove(self):
        if self.last is None:
            return False
        r, c = self.last
        self.dead[r][c] = True
        self.removed[r] += 1
        self.last = None
        return True

    def getVector(self):
        return [list(row) if self.removed[r] == 0 else [v for v, gone in zip(row, self.dead[r]) if not gone]
                for r, row in enumerate(self.rows)]


def solve(operation_names, argument_lists):
    if operation_names[0] != 'Vector2D' or len(argument_lists[0]) != 1:
        raise ValueError('exact initial constructor required')
    instance = Vector2D(*argument_lists[0])
    allowed = {'next', 'hasNext', 'remove', 'getVector'}
    voids = set()
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
