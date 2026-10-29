"""Original Hack2Hire 6abed6282faad6972d969c6f variant over an INFERRED specification; qualification unknown."""


def _digits(field):
    return field != '' and all('0' <= ch <= '9' for ch in field)


def solve(items, k):
    totals = {}
    for item in items:
        fields = item.split('|')
        if len(fields) != 4:
            continue
        sku, name, count, price = fields
        if sku and name and _digits(count) and _digits(price):
            row = totals.setdefault(sku, [name, 0, 0])
            row[1] += int(count)
            row[2] += int(count) * int(price)
    ranked = sorted(totals.items(), key=lambda pair: (-pair[1][2], pair[0]))[:k]
    return [sku + '|' + row[0] + '|' + str(row[1]) + '|' + str(row[2]) for sku, row in ranked]


class Solution:
    def topSkusByCost(self, items, k):
        return solve(items, k)
