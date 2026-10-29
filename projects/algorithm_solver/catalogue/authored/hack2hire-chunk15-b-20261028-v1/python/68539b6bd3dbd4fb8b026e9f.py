"""Hack2Hire 68539b6bd3dbd4fb8b026e9f (Design Lazy Array) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class LazyArray:
    def __init__(self, arr):
        self.size = len(arr)
        self.first = {}
        for i, x in enumerate(arr):
            if x not in self.first:
                self.first[x] = i
        self.a = 1
        self.b = 0

    def map(self, operation, operand):
        if operation == 'add':
            self.b += operand
        else:
            self.a *= operand
            self.b *= operand

    def indexOf(self, target):
        if self.a == 0:
            return 0 if self.size > 0 and self.b == target else -1
        diff = target - self.b
        if diff % self.a != 0:
            return -1
        return self.first.get(diff // self.a, -1)


def solve(operation_names, argument_lists):
    if operation_names[0] != 'LazyArray' or len(argument_lists[0]) != 1:
        raise ValueError('exact initial constructor required')
    instance = LazyArray(*argument_lists[0])
    allowed = {'map', 'indexOf'}
    voids = {'map'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
