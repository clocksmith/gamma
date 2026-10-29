"""Hack2Hire 687c4741aa2b26b0b64b39ee (Design Banking System, variant 2) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""
from bisect import bisect_left

DAY_MS = 86400000


class BankingSystem:
    def __init__(self):
        self.balance = {}
        self.outgoing = {}
        self.rank_keys = []  # sorted (-outgoing, id) of existing accounts
        self.rank_labels = []  # parallel cached 'id(outgoing)' strings

    def _rank_set(self, account, old, new):
        if old is not None:
            index = bisect_left(self.rank_keys, (-old, account))
            del self.rank_keys[index]
            del self.rank_labels[index]
        if new is not None:
            index = bisect_left(self.rank_keys, (-new, account))
            self.rank_keys.insert(index, (-new, account))
            self.rank_labels.insert(index, '%s(%d)' % (account, new))

    def createAccount(self, timestamp, accountId):
        if accountId in self.balance:
            return False
        self.balance[accountId] = 0
        self.outgoing[accountId] = 0
        self._rank_set(accountId, None, 0)
        return True

    def deposit(self, timestamp, accountId, amount):
        if accountId not in self.balance:
            return -1
        self.balance[accountId] += amount
        return self.balance[accountId]

    def transfer(self, timestamp, sourceAccountId, targetAccountId, amount):
        if (sourceAccountId == targetAccountId or sourceAccountId not in self.balance
                or targetAccountId not in self.balance or self.balance[sourceAccountId] < amount):
            return -1
        self.balance[sourceAccountId] -= amount
        self.balance[targetAccountId] += amount
        self._rank_set(sourceAccountId, self.outgoing[sourceAccountId], self.outgoing[sourceAccountId] + amount)
        self.outgoing[sourceAccountId] += amount
        return self.balance[sourceAccountId]

    def topSpenders(self, timestamp, n):
        return self.rank_labels[:n]


def solve(operation_names, argument_lists):
    if operation_names[0] != 'BankingSystem' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = BankingSystem(*argument_lists[0])
    allowed = ['createAccount', 'deposit', 'transfer', 'topSpenders']
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(value)
    return result
