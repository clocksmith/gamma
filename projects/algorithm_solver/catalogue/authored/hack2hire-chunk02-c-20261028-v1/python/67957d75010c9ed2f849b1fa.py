"""Hack2Hire 67957d75010c9ed2f849b1fa (Account Balance Transfer, variant 2) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

from bisect import bisect_right


class TransactionSystem:
    def __init__(self, accounts, transactions):
        self._order = [name for name, _ in accounts]
        balance = {name: amount for name, amount in accounts}
        self._history = {name: ([0], [amount]) for name, amount in accounts}  # (steps, balances)
        for step, (source, target, percent) in enumerate(transactions, 1):
            moved = balance[source] * percent // 100
            balance[source] -= moved
            balance[target] += moved
            for name in (source, target):
                steps, values = self._history[name]
                steps.append(step)
                values.append(balance[name])
        self._balance = balance

    def getBalance(self, name):
        return self._balance.get(name, -1)

    def getBalances(self):
        return [[name, self._balance[name]] for name in self._order]

    def getBalanceAfter(self, name, k):
        if name not in self._history:
            return -1
        steps, values = self._history[name]
        return values[bisect_right(steps, k) - 1]


def solve(operation_names, argument_lists):
    if operation_names[0] != 'TransactionSystem':
        raise ValueError('exact initial constructor required')
    instance = TransactionSystem(*argument_lists[0])
    allowed = ['getBalance', 'getBalances', 'getBalanceAfter']
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        result.append(getattr(instance, name)(*arguments))
    return result
