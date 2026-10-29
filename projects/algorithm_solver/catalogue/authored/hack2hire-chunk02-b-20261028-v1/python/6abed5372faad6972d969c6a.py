"""Original Hack2Hire 6abed5372faad6972d969c6a variant over an INFERRED specification; qualification unknown."""


def _digits(field):
    return field != '' and all('0' <= ch <= '9' for ch in field)


def solve(items):
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
    return [sku + '|' + row[0] + '|' + str(row[1]) + '|' + str(row[2]) for sku, row in sorted(totals.items())]


class Solution:
    def checkoutBySku(self, items):
        return solve(items)
