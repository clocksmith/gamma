"""Hack2Hire 678dc780fa7ce9616e190fb7 (Iterator with Filter) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


_PREDICATES = {
    'even': lambda v: v % 2 == 0,
    'odd': lambda v: v % 2 != 0,
    'positive': lambda v: v > 0,
    'negative': lambda v: v < 0,
    'nonzero': lambda v: v != 0,
}


class FilterIterator:
    def __init__(self, nums, filterName):
        self.nums = nums  # read only
        self.accept = _PREDICATES[filterName]
        self.i = 0

    def hasNext(self):
        while self.i < len(self.nums) and not self.accept(self.nums[self.i]):
            self.i += 1
        return self.i < len(self.nums)

    def next(self):
        self.hasNext()
        value = self.nums[self.i]
        self.i += 1
        return value


def solve(operation_names, argument_lists):
    if operation_names[0] != 'FilterIterator' or len(argument_lists[0]) != 2:
        raise ValueError('exact initial constructor required')
    instance = FilterIterator(*argument_lists[0])
    allowed = {'hasNext', 'next'}
    voids = set()
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
