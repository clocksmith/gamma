"""585. Investments in 2016. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. insurance: pid, tiv_2015, tiv_2016, lat, lon. Output: tiv_2016. Decimal summation rounds once; SUM over no qualifying rows is NULL."""

from decimal import Decimal, ROUND_HALF_UP, localcontext

def solve(insurance):
    values, positions = {}, {}
    for row in insurance:
        value, position = row['tiv_2015'], (row['lat'], row['lon'])
        values[value] = values.get(value, 0) + 1
        positions[position] = positions.get(position, 0) + 1
    selected = [row['tiv_2016'] for row in insurance
                if values[row['tiv_2015']] > 1 and positions[(row['lat'], row['lon'])] == 1]
    if not selected:
        return [{'tiv_2016': None}]
    with localcontext() as context:
        context.prec = 60
        total = sum((Decimal(str(value)) for value in selected), Decimal(0))
        return [{'tiv_2016': float(total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))}]


class Solution:
    def investments(self, insurance):
        return solve(insurance)
