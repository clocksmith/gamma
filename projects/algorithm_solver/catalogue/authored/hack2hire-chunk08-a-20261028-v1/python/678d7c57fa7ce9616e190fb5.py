"""Hack2Hire 678d7c57fa7ce9616e190fb5 (Range Iterator) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class RangeIterator:
    def __init__(self, start, end, step):
        self.current = start
        self.end = end
        self.step = step

    def hasNext(self):
        return self.current < self.end if self.step > 0 else self.current > self.end

    def next(self):
        value = self.current
        self.current += self.step
        return value


def solve(operation_names, argument_lists):
    if operation_names[0] != 'RangeIterator' or len(argument_lists[0]) != 3:
        raise ValueError('exact initial constructor required')
    instance = RangeIterator(*argument_lists[0])
    allowed = {'hasNext', 'next'}
    voids = set()
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
