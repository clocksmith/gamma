def solve(num, sum):
    if sum > 9 * num:
        return ''
    q, r = divmod(sum, 9)
    return '9' * q + (str(r) if r else '') + '0' * (num - q - bool(r))


class Solution:
    def maxSumOfSquares(self, num, sum):
        return solve(num, sum)
