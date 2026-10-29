"""Hack2Hire 687c3a5eaa2b26b0b64b39e5 (Design Banking System, variant 1) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

DAY_MS = 86400000


class BankingSystem:
    def __init__(self):
        self.balance = {}

    def createAccount(self, timestamp, accountId):
        if accountId in self.balance:
            return False
        self.balance[accountId] = 0
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
        return self.balance[sourceAccountId]


def solve(operation_names, argument_lists):
    if operation_names[0] != 'BankingSystem' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = BankingSystem(*argument_lists[0])
    allowed = ['createAccount', 'deposit', 'transfer']
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(value)
    return result
