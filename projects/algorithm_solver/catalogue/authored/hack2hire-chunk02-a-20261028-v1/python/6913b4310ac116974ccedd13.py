"""Hack2Hire 6913b4310ac116974ccedd13 (GPU Credits II); INFERRED spec; qualification unknown."""
import heapq


class CreditSystem:
    def __init__(self):
        self.grants = []    # (start, end, creditId, amount)
        self.consumes = []  # (timestamp, arrival, amount)

    def _replay(self, until, stop_arrival=None):
        """Sweep events with time <= until; returns (active total at `until`, success of stop_arrival)."""
        grants = sorted(g for g in self.grants if g[0] <= until)
        consumes = sorted(c for c in self.consumes if c[0] <= until and (stop_arrival is None or c[0] < until or c[1] <= stop_arrival))
        heap, total, gi, outcome = [], 0, 0, None
        remaining = {}

        def advance(t):
            nonlocal gi, total
            while gi < len(grants) and grants[gi][0] <= t:
                start, end, cid, amount = grants[gi]; gi += 1
                remaining[cid] = amount; total += amount
                heapq.heappush(heap, (end, start, cid))
            while heap and heap[0][0] < t:
                total -= remaining[heapq.heappop(heap)[2]]
        for t, arrival, amount in consumes:
            advance(t)
            ok = total >= amount
            if ok:
                total -= amount
                while amount:
                    end, start, cid = heap[0]
                    take = min(amount, remaining[cid])
                    remaining[cid] -= take; amount -= take
                    if remaining[cid] == 0: heapq.heappop(heap)
            if arrival == stop_arrival: outcome = ok
        advance(until)
        return total, outcome

    def addCredit(self, creditId, amount, startTime, endTime):
        self.grants.append((startTime, endTime, creditId, amount))

    def consumeCredit(self, amount, timestamp):
        arrival = len(self.consumes)
        self.consumes.append((timestamp, arrival, amount))
        return self._replay(timestamp, arrival)[1]

    def getBalance(self, timestamp):
        return self._replay(timestamp)[0]


def solve(operations, arguments):
    system = CreditSystem(*arguments[0])
    return [None] + [getattr(system, op)(*row) for op, row in zip(operations[1:], arguments[1:])]
