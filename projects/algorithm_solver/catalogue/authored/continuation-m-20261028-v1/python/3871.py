def solve(n):
    answer = 0
    threshold = 1000
    while threshold <= n:
        answer += n - threshold + 1
        threshold *= 1000
    return answer


class Solution:
    def countCommas(self, n):
        return solve(n)
