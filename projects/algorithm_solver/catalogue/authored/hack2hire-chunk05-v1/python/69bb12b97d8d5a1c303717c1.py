"""Original hack2hire:69bb12b97d8d5a1c303717c1; inferred public-preview contract; qualification unknown."""
from heapq import heappush, heappop

class TradingSystem:
    def __init__(self):
        self.items = {}
        self.sequence = 0

    def addListing(self, seller, item, price):
        heappush(self.items.setdefault(item, []), (price, self.sequence, seller))
        self.sequence += 1

    def buy(self, item, budget):
        queue = self.items.get(item, [])
        if not queue or queue[0][0] > budget:
            return None
        price, sequence, seller = heappop(queue)
        return [seller, price]

def solve(operation_names, argument_lists):
    if len(operation_names) != len(argument_lists) or not operation_names or operation_names[0] != 'TradingSystem':
        raise ValueError("exact constructor trace required")
    instance = TradingSystem(*argument_lists[0])
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in ('addListing', 'buy'):
            raise ValueError("unknown method")
        result.append(getattr(instance, name)(*arguments))
    return result
