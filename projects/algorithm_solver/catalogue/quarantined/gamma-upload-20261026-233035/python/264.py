"""264. Ugly Number II."""
def solve(n: int) -> int:
    values = [1] * n
    index2 = index3 = index5 = 0
    for index in range(1, n):
        next_value = min(values[index2] * 2, values[index3] * 3, values[index5] * 5)
        values[index] = next_value
        if next_value == values[index2] * 2:
            index2 += 1
        if next_value == values[index3] * 3:
            index3 += 1
        if next_value == values[index5] * 5:
            index5 += 1
    return values[-1]

class Solution:
    def nthUglyNumber(self, n: int) -> int:
        return solve(n)
