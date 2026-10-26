"""1306. Jump Game III: search reachable indices without marking the input array."""


def solve(arr: list[int], start: int) -> bool:
    """O(n) time and O(n) auxiliary space; inputs are read-only."""
    seen = [False] * len(arr)
    seen[start] = True
    stack = [start]
    while stack:
        index = stack.pop()
        if arr[index] == 0:
            return True
        for following in (index - arr[index], index + arr[index]):
            if 0 <= following < len(arr) and not seen[following]:
                seen[following] = True
                stack.append(following)
    return False


class Solution:
    def canReach(self, arr: list[int], start: int) -> bool:
        return solve(arr, start)
