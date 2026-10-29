"""Hack2Hire 6a629dc8190ed618c6e6b223 (Aggregate Recent Transactions) over an INFERRED spec; qualification unknown."""


def cents(amount):
    whole, _, fraction = amount.partition('.')
    return int(whole) * 100 + int((fraction + '00')[:2])


def solve(transactions, currentTime):
    now = int(currentTime)
    totals = {}
    for amount, merchant, status, _, start in transactions:
        hours = (now - int(start)) // 3600
        if status == 'COMPLETED' and 0 <= hours < 24:
            entry = totals.setdefault(merchant, [0, 0])
            entry[0] += cents(amount)
            entry[1] += 1
    return [[m, '%d.%02d' % divmod(totals[m][0], 100), totals[m][1]] for m in sorted(totals)]


class Solution:
    def aggregateRecent(self, transactions, currentTime):
        return solve(transactions, currentTime)
