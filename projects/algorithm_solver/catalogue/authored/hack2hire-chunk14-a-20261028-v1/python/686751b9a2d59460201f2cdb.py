"""Hack2Hire 686751b9a2d59460201f2cdb (Top K Book Sales) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

from bisect import bisect_left, insort


class BookSalesTracker:
    def __init__(self):
        self.totals = {}
        self.order = []

    def recordSale(self, bookId, quantity):
        old = self.totals.get(bookId)
        if old is not None:
            del self.order[bisect_left(self.order, (-old, bookId))]
        new = (old or 0) + quantity
        self.totals[bookId] = new
        insort(self.order, (-new, bookId))

    def getTopK(self, k):
        return [bookId for _, bookId in self.order[:k]]


def solve(operation_names, argument_lists):
    if operation_names[0] != 'BookSalesTracker' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = BookSalesTracker(*argument_lists[0])
    allowed = {'recordSale', 'getTopK'}
    voids = {'recordSale'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
