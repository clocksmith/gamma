"""Hack2Hire 69117148869dd6a56c434054 (GPU Credits); INFERRED spec; qualification unknown."""


class CreditSystem:
    def __init__(self):
        self.grants = {}  # id -> [amount, start, end, revokedAt or None]

    def addCredit(self, creditId, amount, startTime, endTime):
        self.grants[creditId] = [amount, startTime, endTime, None]

    def revokeCredit(self, creditId, timestamp):
        grant = self.grants.get(creditId)
        if grant is None or grant[3] is not None: return False
        grant[3] = timestamp
        return True

    def getBalance(self, timestamp):
        total = 0
        for amount, start, end, revoked in self.grants.values():
            if start <= timestamp <= end and (revoked is None or timestamp < revoked): total += amount
        return total


def solve(operations, arguments):
    system = CreditSystem(*arguments[0])
    return [None] + [getattr(system, op)(*row) for op, row in zip(operations[1:], arguments[1:])]
