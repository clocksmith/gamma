"""Hack2Hire 6917944f10632c00111ca218 (Delivery Cost Calculate, variant 3) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""
from bisect import bisect_left, bisect_right
import heapq

SPAN = 1 << 30  # time domain [0, 2**30) covers every inferred instant (<= 1e9)


class _MaxTree:
    """Dynamic segment tree: range add, range max; absent children hold zero."""

    def __init__(self):
        self.left, self.right, self.best, self.add = [-1], [-1], [0], [0]

    def _child(self, node, side):
        links = self.left if side == 0 else self.right
        if links[node] < 0:
            links[node] = len(self.best)
            self.left.append(-1); self.right.append(-1); self.best.append(0); self.add.append(0)
        return links[node]

    def update(self, low, high, delta, node=0, lo=0, hi=SPAN - 1):
        if low <= lo and hi <= high:
            self.add[node] += delta
            self.best[node] += delta
            return
        mid = (lo + hi) // 2
        if low <= mid:
            self.update(low, high, delta, self._child(node, 0), lo, mid)
        if high > mid:
            self.update(low, high, delta, self._child(node, 1), mid + 1, hi)
        left, right = self.left[node], self.right[node]
        self.best[node] = self.add[node] + max(self.best[left] if left >= 0 else 0, self.best[right] if right >= 0 else 0)

    def query(self, low, high, node=0, lo=0, hi=SPAN - 1):
        if node < 0:
            return 0
        if low <= lo and hi <= high:
            return self.best[node]
        mid = (lo + hi) // 2
        result = 0
        if low <= mid:
            result = self.query(low, high, self.left[node], lo, mid)
        if high > mid:
            result = max(result, self.query(low, high, self.right[node], mid + 1, hi))
        return self.add[node] + result


def _money(scaled):
    """scaled = sum of rateCents * seconds; exact cents = scaled / 3600, rounded half-up."""
    cents = (2 * scaled + 3600) // 7200
    return '%d.%02d' % (cents // 100, cents % 100)


class DeliverySystem:
    def __init__(self):
        self.rates = {}
        self.total = 0
        self.unpaid = 0
        self.unpaid_heap = []
        self.unions = {}  # driver -> (starts, ends) of its disjoint merged delivery intervals
        self.coverage = _MaxTree()  # distinct active drivers per instant

    def addDriver(self, driverId, hourlyRateCents):
        self.rates[driverId] = hourlyRateCents

    def addDelivery(self, driverId, startTime, endTime):
        scaled = self.rates[driverId] * (endTime - startTime)
        self.total += scaled
        self.unpaid += scaled
        heapq.heappush(self.unpaid_heap, (endTime, scaled))
        starts, ends = self.unions.setdefault(driverId, ([], []))
        first = bisect_left(ends, startTime)  # first union ending at or after the start (touching merges)
        last = bisect_right(starts, endTime)  # unions starting at or before the end
        low, high = startTime, endTime
        for k in range(first, last):
            self.coverage.update(starts[k], ends[k] - 1, -1)
            low, high = min(low, starts[k]), max(high, ends[k])
        starts[first:last] = [low]
        ends[first:last] = [high]
        self.coverage.update(low, high - 1, 1)

    def getTotalCost(self):
        return _money(self.total)

    def payUpTo(self, upToTime):
        while self.unpaid_heap and self.unpaid_heap[0][0] <= upToTime:
            self.unpaid -= heapq.heappop(self.unpaid_heap)[1]

    def getTotalCostUnpaid(self):
        return _money(self.unpaid)

    def getMaxActiveDriversInLast24Hours(self, currentTime):
        return self.coverage.query(max(currentTime - 86400, 0), currentTime)


def solve(operation_names, argument_lists):
    if operation_names[0] != 'DeliverySystem' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = DeliverySystem(*argument_lists[0])
    allowed = ['addDriver', 'addDelivery', 'getTotalCost', 'payUpTo', 'getTotalCostUnpaid', 'getMaxActiveDriversInLast24Hours']
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(value)
    return result
