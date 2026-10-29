"""Hack2Hire 69cda519ff3ebde766cee834 (Object Field Offset Manager) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class ObjectLayout:
    def __init__(self, names, sizes):
        self.slot_names = list(names)
        self.sizes = list(sizes)
        self.slot = {name: i for i, name in enumerate(self.slot_names)}
        self.total = sum(self.sizes)
        self._rebuild(max(1, len(self.sizes)))

    def _rebuild(self, capacity):
        self.capacity = capacity
        tree = [0] * (capacity + 1)
        for i, s in enumerate(self.sizes):
            tree[i + 1] += s
        for i in range(1, capacity + 1):
            j = i + (i & -i)
            if j <= capacity:
                tree[j] += tree[i]
        self.tree = tree

    def _add(self, index, delta):
        i = index + 1
        while i <= self.capacity:
            self.tree[i] += delta
            i += i & -i

    def _before(self, index):
        i = index
        total = 0
        while i > 0:
            total += self.tree[i]
            i -= i & -i
        return total

    def getOffset(self, name):
        index = self.slot.get(name)
        return -1 if index is None else self._before(index)

    def fieldAt(self, offset):
        if offset >= self.total:
            return ''
        position = 0
        remaining = offset
        step = 1
        while step * 2 <= self.capacity:
            step *= 2
        while step:
            nxt = position + step
            if nxt <= self.capacity and self.tree[nxt] <= remaining:
                position = nxt
                remaining -= self.tree[nxt]
            step //= 2
        return self.slot_names[position]

    def totalSize(self):
        return self.total

    def addField(self, name, size):
        if name in self.slot:
            return False
        index = len(self.sizes)
        self.slot_names.append(name)
        self.sizes.append(size)
        self.slot[name] = index
        self.total += size
        if index >= self.capacity:
            self._rebuild(self.capacity * 2)
        else:
            self._add(index, size)
        return True

    def removeField(self, name):
        index = self.slot.pop(name, None)
        if index is None:
            return False
        self._add(index, -self.sizes[index])
        self.total -= self.sizes[index]
        self.sizes[index] = 0
        return True


def solve(operation_names, argument_lists):
    if operation_names[0] != 'ObjectLayout' or len(argument_lists[0]) != 2:
        raise ValueError('exact initial constructor required')
    instance = ObjectLayout(*argument_lists[0])
    allowed = {'getOffset', 'fieldAt', 'totalSize', 'addField', 'removeField'}
    voids = set()
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
