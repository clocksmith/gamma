"""Original development candidate; independent qualification pending."""
def solve(digits, n):
    s = str(n)
    count = len(digits)
    answer = sum(count**size for size in range(1,len(s)))
    for i,ch in enumerate(s):
        answer += sum(d < ch for d in digits)*count**(len(s)-i-1)
        if ch not in digits:
            return answer
    return answer+1


class Solution:
    def atMostNGivenDigitSet(self, digits, n):
        return solve(digits, n)
