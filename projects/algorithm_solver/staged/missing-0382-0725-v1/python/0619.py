"""619. Biggest Single Number. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. my_numbers: num, duplicates allowed. Output: num; no single number yields NULL."""

def solve(my_numbers):
    counts = {}
    for row in my_numbers:
        value = row['num']
        counts[value] = counts.get(value, 0) + 1
    return [{'num': max((value for value, count in counts.items() if value is not None and count == 1), default=None)}]


class Solution:
    def biggestSingleNumber(self, my_numbers):
        return solve(my_numbers)
