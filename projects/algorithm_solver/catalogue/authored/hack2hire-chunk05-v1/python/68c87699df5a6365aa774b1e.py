"""Original hack2hire:68c87699df5a6365aa774b1e; inferred public-preview contract; qualification unknown."""
from math import gcd
from functools import cmp_to_key

class CustomerSupportSystem:
    def __init__(self):
        self.all = {}
        self.months = {}

    def record(self, agentId, score, month):
        for target in (self.all, self.months.setdefault(month, {})):
            total, count = target.get(agentId, (0, 0))
            target[agentId] = (total + score, count + 1)

    def rank(self, month):
        rows = self.all if month is None else self.months.get(month, {})
        def compare(a, b):
            x, nx = rows[a]
            y, ny = rows[b]
            difference = x * ny - y * nx
            return -1 if difference > 0 else 1 if difference < 0 else (a > b) - (a < b)
        result = []
        for agent in sorted(rows, key=cmp_to_key(compare)):
            total, count = rows[agent]
            divisor = gcd(total, count)
            result.append([agent, total // divisor, count // divisor])
        return result

def solve(operation_names, argument_lists):
    if len(operation_names) != len(argument_lists) or not operation_names or operation_names[0] != 'CustomerSupportSystem':
        raise ValueError("exact constructor trace required")
    instance = CustomerSupportSystem(*argument_lists[0])
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in ('record', 'rank'):
            raise ValueError("unknown method")
        result.append(getattr(instance, name)(*arguments))
    return result
