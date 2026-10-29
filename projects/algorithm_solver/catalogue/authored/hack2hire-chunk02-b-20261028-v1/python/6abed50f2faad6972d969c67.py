"""Original Hack2Hire 6abed50f2faad6972d969c67 variant over an INFERRED specification; qualification unknown."""


def _digits(field):
    return field != '' and all('0' <= ch <= '9' for ch in field)


def solve(items):
    quantity = cost = 0
    for item in items:
        fields = item.split('|')
        if len(fields) != 4:
            continue
        sku, name, count, price = fields
        if sku and name and _digits(count) and _digits(price):
            quantity += int(count)
            cost += int(count) * int(price)
    return [quantity, cost]


class Solution:
    def checkoutTotals(self, items):
        return solve(items)
