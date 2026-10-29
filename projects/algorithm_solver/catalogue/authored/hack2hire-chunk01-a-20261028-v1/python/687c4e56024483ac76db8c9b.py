"""Hack2Hire 687c4e56024483ac76db8c9b (Design Banking System, variant 3) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""
from bisect import bisect_left
from collections import deque

DAY_MS = 86400000


class BankingSystem:
    def __init__(self):
        self.balance = {}
        self.outgoing = {}
        self.rank_keys = []  # sorted (-outgoing, id) of existing accounts
        self.rank_labels = []  # parallel cached 'id(outgoing)' strings
        self.payments = {}  # payment id -> [owner, amount, status]
        self.owned = {}  # account -> list of payment ids it owns
        self.cashbacks = deque()  # (due time, payment id); due times increase with timestamps
        self.payment_count = 0

    def _settle(self, timestamp):
        while self.cashbacks and self.cashbacks[0][0] <= timestamp:
            due, payment = self.cashbacks.popleft()
            record = self.payments[payment]
            self.balance[record[0]] += record[1] * 2 // 100
            record[2] = 'CASHBACK_RECEIVED'

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
        self._settle(timestamp)
        if accountId in self.balance:
            return False
        self.balance[accountId] = 0
        self.outgoing[accountId] = 0
        self._rank_set(accountId, None, 0)
        self.owned[accountId] = []
        return True

    def deposit(self, timestamp, accountId, amount):
        self._settle(timestamp)
        if accountId not in self.balance:
            return -1
        self.balance[accountId] += amount
        return self.balance[accountId]

    def transfer(self, timestamp, sourceAccountId, targetAccountId, amount):
        self._settle(timestamp)
        if (sourceAccountId == targetAccountId or sourceAccountId not in self.balance
                or targetAccountId not in self.balance or self.balance[sourceAccountId] < amount):
            return -1
        self.balance[sourceAccountId] -= amount
        self.balance[targetAccountId] += amount
        self._rank_set(sourceAccountId, self.outgoing[sourceAccountId], self.outgoing[sourceAccountId] + amount)
        self.outgoing[sourceAccountId] += amount
        return self.balance[sourceAccountId]

    def topSpenders(self, timestamp, n):
        self._settle(timestamp)
        return self.rank_labels[:n]

    def pay(self, timestamp, accountId, amount):
        self._settle(timestamp)
        if accountId not in self.balance or self.balance[accountId] < amount:
            return None
        self.balance[accountId] -= amount
        self._rank_set(accountId, self.outgoing[accountId], self.outgoing[accountId] + amount)
        self.outgoing[accountId] += amount
        self.payment_count += 1
        payment = 'payment' + str(self.payment_count)
        self.payments[payment] = [accountId, amount, 'IN_PROGRESS']
        self.owned[accountId].append(payment)
        self.cashbacks.append((timestamp + DAY_MS, payment))
        return payment

    def getPaymentStatus(self, timestamp, accountId, payment):
        self._settle(timestamp)
        record = self.payments.get(payment)
        if accountId not in self.balance or record is None or record[0] != accountId:
            return None
        return record[2]


def solve(operation_names, argument_lists):
    if operation_names[0] != 'BankingSystem' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = BankingSystem(*argument_lists[0])
    allowed = ['createAccount', 'deposit', 'transfer', 'topSpenders', 'pay', 'getPaymentStatus']
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(value)
    return result
