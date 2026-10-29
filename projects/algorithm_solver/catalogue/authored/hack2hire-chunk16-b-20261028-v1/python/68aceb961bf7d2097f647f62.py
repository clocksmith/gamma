"""Hack2Hire 68aceb961bf7d2097f647f62 (Product Price Tracker) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

import heapq


class ProductPrice:
    def __init__(self):
        self.prices = {}
        self.latest = 0
        self.high = []  # (-price, timestamp)
        self.low = []  # (price, timestamp)

    def update(self, timestamp, price):
        self.prices[timestamp] = price
        if timestamp > self.latest:
            self.latest = timestamp
        heapq.heappush(self.high, (-price, timestamp))
        heapq.heappush(self.low, (price, timestamp))

    def current(self):
        return self.prices[self.latest] if self.prices else -1

    def maximum(self):
        while self.high and self.prices[self.high[0][1]] != -self.high[0][0]:
            heapq.heappop(self.high)
        return -self.high[0][0] if self.high else -1

    def minimum(self):
        while self.low and self.prices[self.low[0][1]] != self.low[0][0]:
            heapq.heappop(self.low)
        return self.low[0][0] if self.low else -1


def solve(operation_names, argument_lists):
    if operation_names[0] != 'ProductPrice' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = ProductPrice(*argument_lists[0])
    allowed = {'update', 'current', 'maximum', 'minimum'}
    voids = {'update'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
