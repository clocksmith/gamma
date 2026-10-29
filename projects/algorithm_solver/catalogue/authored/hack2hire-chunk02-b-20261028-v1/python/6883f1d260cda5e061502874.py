"""Original Hack2Hire 6883f1d260cda5e061502874 variant over an INFERRED specification; qualification unknown."""


def _cents(amount):
    whole, _, fraction = amount.partition('.')
    return int(whole) * 100 + int((fraction + '00')[:2])


def _format(cents):
    sign = '-' if cents < 0 else ''
    cents = abs(cents)
    return sign + str(cents // 100) + '.' + str(cents % 100).zfill(2)


def solve(records):
    column = {name: i for i, name in enumerate(records[0])}
    p, d, c, s = column['product'], column['date'], column['cost'], column['sell_price']
    profit, months = {}, set()
    for row in records[1:]:
        month = row[d][:7]
        months.add(month)
        key = (row[p], month)
        profit[key] = profit.get(key, 0) + _cents(row[s]) - _cents(row[c])
    months = sorted(months)
    table = [['product'] + months]
    for product in sorted({key[0] for key in profit}):
        table.append([product] + [_format(profit.get((product, month), 0)) for month in months])
    return table


class Solution:
    def pivotProfit(self, records):
        return solve(records)
