"""Hack2Hire 6aa32de80ca9cc4e1c7903a3 (Referral Credit Tracker, level 2) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

from heapq import heappop, heappush

class AccountCreditTracker:
    def __init__(self):
        self.totals = []
        self.heap = []

    def addAccount(self, credit):
        self.totals.append(credit)
        self._touch(len(self.totals) - 1)
        return len(self.totals) - 1

    def addAccountWithReferral(self, credit, referrerId):
        self.totals[referrerId] += credit
        self._touch(referrerId)
        return self.addAccount(credit)

    def getTotalCredit(self, accountId):
        return self.totals[accountId]

    def _touch(self, account):
        heappush(self.heap, (-self.totals[account], account))

    def getTopAccounts(self, k):
        chosen, seen = [], set()
        while self.heap and len(chosen) < k:
            negative, account = heappop(self.heap)
            if -negative != self.totals[account] or account in seen:
                continue
            seen.add(account)
            chosen.append(account)
        for account in chosen:
            heappush(self.heap, (-self.totals[account], account))
        return chosen


def solve(operation_names, argument_lists):
    if operation_names[0] != 'AccountCreditTracker' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = AccountCreditTracker(*argument_lists[0])
    allowed = ['addAccount', 'addAccountWithReferral', 'getTotalCredit', 'getTopAccounts']
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in [] else value)
    return result
