"""571. Find Median Given Frequency of Numbers. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. numbers: num, frequency. Output: median. Frequencies are nonnegative; no decompressed array is allocated."""

from decimal import Decimal, ROUND_HALF_UP, localcontext


def _rounded_ratio(numerator, denominator, places):
    with localcontext() as context:
        context.prec = 60
        value = Decimal(numerator) / Decimal(denominator)
        return float(value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP))

def solve(numbers):
    total = sum(row['frequency'] for row in numbers)
    if total == 0:
        return [{'median': None}]
    targets = [(total + 1) // 2, total // 2 + 1]
    cumulative, selected = 0, []
    for row in sorted(numbers, key=lambda item: item['num']):
        previous = cumulative
        cumulative += row['frequency']
        for rank in targets:
            if previous < rank <= cumulative:
                selected.append(row['num'])
    return [{'median': _rounded_ratio(sum(selected), 2, 1)}]


class Solution:
    def medianFrequency(self, numbers):
        return solve(numbers)
