"""Hack2Hire 677bf4df5cbaff553b53b068 (Subarray-First Iterator) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class SubarrayFirstIterator:
    def __init__(self, a, b):
        self.a, self.b = a, b
        self.excluded = set(b)
        self.i = 0
        self.j = 0

    def hasNext(self):
        if self.i < len(self.b):
            return True
        a, excluded = self.a, self.excluded
        while self.j < len(a) and a[self.j] in excluded:
            self.j += 1
        return self.j < len(a)

    def next(self):
        if self.i < len(self.b):
            self.i += 1
            return self.b[self.i - 1]
        self.hasNext()
        self.j += 1
        return self.a[self.j - 1]


def solve(operation_names, argument_lists):
    if operation_names[0] != 'SubarrayFirstIterator' or len(argument_lists[0]) != 2:
        raise ValueError('exact initial constructor required')
    instance = SubarrayFirstIterator(*argument_lists[0])
    allowed = ['hasNext', 'next']
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in [] else value)
    return result
