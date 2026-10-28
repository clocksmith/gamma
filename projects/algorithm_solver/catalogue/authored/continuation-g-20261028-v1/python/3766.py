from bisect import bisect_left


def solve(nums):
    limit = 2 * max(nums) + 1
    palindromes = []
    for x in range(limit + 1):
        text = bin(x)[2:]
        if text == text[::-1]:
            palindromes.append(x)
    answer = []
    for x in nums:
        i = bisect_left(palindromes, x)
        distance = x - palindromes[i - 1]
        if i < len(palindromes):
            distance = min(distance, palindromes[i] - x)
        answer.append(distance)
    return answer


class Solution:
    def minOperations(self, nums):
        return solve(nums)
