"""Hack2Hire 69445eb8867a3f9f539ff53d (Customer Revenue System, variant 2) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

from bisect import bisect_left, insort


class CustomerRevenueSystem:
    def __init__(self):
        self._own = []
        self._total = []
        self._children = []
        self._ranked = []  # sorted (total, id)

    def _add(self, revenue):
        customer = len(self._own)
        self._own.append(revenue)
        self._total.append(revenue)
        self._children.append([])
        insort(self._ranked, (revenue, customer))
        return customer

    def insert(self, revenue):
        return self._add(revenue)

    def insertWithReferrer(self, revenue, referrerId):
        customer = self._add(revenue)
        self._children[referrerId].append(customer)
        old = (self._total[referrerId], referrerId)
        del self._ranked[bisect_left(self._ranked, old)]
        self._total[referrerId] += revenue
        insort(self._ranked, (self._total[referrerId], referrerId))
        return customer

    def getLowestK(self, k, minTotal):
        start = bisect_left(self._ranked, (minTotal, -1))
        return [customer for _, customer in self._ranked[start:start + k]]

    def getNestedRevenue(self, customerId, maxDepth):
        queue, depths, total, head = [customerId], [0], 0, 0
        while head < len(queue):
            customer, depth = queue[head], depths[head]
            head += 1
            total += self._own[customer]
            if depth < maxDepth:
                for child in self._children[customer]:
                    queue.append(child)
                    depths.append(depth + 1)
        return total


def solve(operation_names, argument_lists):
    if operation_names[0] != 'CustomerRevenueSystem':
        raise ValueError('exact initial constructor required')
    instance = CustomerRevenueSystem(*argument_lists[0])
    allowed = ['insert', 'insertWithReferrer', 'getLowestK', 'getNestedRevenue']
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        result.append(getattr(instance, name)(*arguments))
    return result
