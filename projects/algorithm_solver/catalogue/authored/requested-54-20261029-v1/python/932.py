"""Original development candidate; independent qualification pending."""
def solve(n):
    answer = [1]
    while len(answer) < n:
        answer = [2*x-1 for x in answer if 2*x-1 <= n]+[2*x for x in answer if 2*x <= n]
    return answer


class Solution:
    def beautifulArray(self, n):
        return solve(n)
