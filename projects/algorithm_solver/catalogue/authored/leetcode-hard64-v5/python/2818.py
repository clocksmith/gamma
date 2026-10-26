"""2818. Apply Operations to Maximize Score. Count prime-score ownership intervals, then take the largest available factors."""


def solve(nums: list[int], k: int) -> int:
    """O(M log log(M+2)+n log n+n log(k+1)) time and O(M+n) space, M=max(nums). Inputs are preserved."""
    modulus = 1_000_000_007
    maximum = max(nums)
    scores = [0] * (maximum + 1)
    for prime in range(2, maximum + 1):
        if scores[prime] == 0:
            for multiple in range(prime, maximum + 1, prime):
                scores[multiple] += 1
    size = len(nums)
    left = [-1] * size
    right = [size] * size
    stack = []
    for index in range(size):
        while stack and scores[nums[stack[-1]]] < scores[nums[index]]:
            stack.pop()
        if stack:
            left[index] = stack[-1]
        stack.append(index)
    stack.clear()
    for index in range(size - 1, -1, -1):
        while stack and scores[nums[stack[-1]]] <= scores[nums[index]]:
            stack.pop()
        if stack:
            right[index] = stack[-1]
        stack.append(index)
    answer = 1
    remaining = k
    for index in sorted(range(size), key=nums.__getitem__, reverse=True):
        uses = min(remaining, (index - left[index]) * (right[index] - index))
        answer = answer * pow(nums[index], uses, modulus) % modulus
        remaining -= uses
        if remaining == 0:
            break
    return answer


class Solution:
    def maximumScore(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
