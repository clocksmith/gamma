"""Hack2Hire 67957d70010c9ed2f849b1f9 (Account Balance Transfer, variant 1) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

class TransactionSystem:
    def __init__(self, accounts, transactions):
        self._order = [name for name, _ in accounts]
        balance = {name: amount for name, amount in accounts}
        for source, target, percent in transactions:
            moved = balance[source] * percent // 100
            balance[source] -= moved
            balance[target] += moved
        self._balance = balance

    def getBalance(self, name):
        return self._balance.get(name, -1)

    def getBalances(self):
        return [[name, self._balance[name]] for name in self._order]


def solve(operation_names, argument_lists):
    if operation_names[0] != 'TransactionSystem':
        raise ValueError('exact initial constructor required')
    instance = TransactionSystem(*argument_lists[0])
    allowed = ['getBalance', 'getBalances']
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        result.append(getattr(instance, name)(*arguments))
    return result
