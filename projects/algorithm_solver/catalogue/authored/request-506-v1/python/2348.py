# Original candidate implementation. Contract: https://leetcode.com/problems/number-of-zero-filled-subarrays/
def solve(nums):
    answer = run = 0
    for value in nums:
        run = run + 1 if value == 0 else 0
        answer += run
    return answer
