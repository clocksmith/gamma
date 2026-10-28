def solve(nums):
    best = [[], [], []]
    for x in nums:
        group = best[x % 3]
        group.append(x)
        group.sort(reverse=True)
        if len(group) > 3:
            group.pop()
    answer = 0
    for group in best:
        if len(group) == 3:
            answer = max(answer, sum(group))
    if all(best):
        answer = max(answer, best[0][0] + best[1][0] + best[2][0])
    return answer


class Solution:
    def maximumSum(self, nums):
        return solve(nums)
