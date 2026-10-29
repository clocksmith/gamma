"""Hack2Hire 6a5941a8665efda9311fa417 (Live Fraud Detector, v1); INFERRED spec; qualification unknown."""


class DistinctPIIValuesCounter:
    def __init__(self):
        self.seen = set()

    def processEvent(self, event):
        for field in range(1, 5):
            if event[field] != '': self.seen.add((field, event[field]))

    def getDistinctPIICount(self):
        return len(self.seen)


def solve(operations, arguments):
    counter = DistinctPIIValuesCounter(*arguments[0])
    return [None] + [getattr(counter, op)(*row) for op, row in zip(operations[1:], arguments[1:])]
