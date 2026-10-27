"""457. Circular Array Loop. Find same-direction cycles excluding self-loops; O(n) total visits, input preserved."""

def solve(nums: list[int]) -> bool:
    n = len(nums)
    done = [False] * n
    for start in range(n):
        if done[start]:
            continue
        positive = nums[start] > 0
        local = set()
        node = start
        while not done[node] and (nums[node] > 0) == positive:
            if node in local:
                return True
            local.add(node)
            following = (node + nums[node]) % n
            if following == node:
                break
            node = following
        for node in local:
            done[node] = True
    return False


class Solution:
    def circularArrayLoop(self, nums: list[int]) -> bool:
        return solve(nums)
