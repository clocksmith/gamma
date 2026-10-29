"""Hack2Hire 68dc6c86dd5418be11109b14 (Stock Trade Ranking System) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class StockTracker:
    def __init__(self):
        self.totals = {}
        self.ranking = []
        self.dirty = False

    def recordTrade(self, stockName, quantity):
        self.totals[stockName] = self.totals.get(stockName, 0) + quantity
        self.dirty = True

    def getRankedStocks(self):
        if self.dirty:
            totals = self.totals
            self.ranking = sorted(totals, key=lambda name: (-totals[name], name))
            self.dirty = False
        return list(self.ranking)


def solve(operation_names, argument_lists):
    if operation_names[0] != 'StockTracker' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = StockTracker(*argument_lists[0])
    allowed = {'recordTrade', 'getRankedStocks'}
    voids = {'recordTrade'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
