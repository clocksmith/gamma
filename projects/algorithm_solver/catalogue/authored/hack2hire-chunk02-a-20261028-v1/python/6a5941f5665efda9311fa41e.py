"""Hack2Hire 6a5941f5665efda9311fa41e (Live Fraud Detector, v2); INFERRED spec; qualification unknown."""


class DistinctPIIValuesCounter:
    def __init__(self):
        self.events = {}
        self.shared = 0

    def processEvent(self, event):
        for value in {(field, event[field]) for field in range(1, 5) if event[field] != ''}:
            count = self.events.get(value, 0) + 1
            self.events[value] = count
            if count == 2: self.shared += 1

    def getDistinctPIICount(self):
        return len(self.events)

    def getSharedPIICount(self):
        return self.shared


def solve(operations, arguments):
    counter = DistinctPIIValuesCounter(*arguments[0])
    return [None] + [getattr(counter, op)(*row) for op, row in zip(operations[1:], arguments[1:])]
