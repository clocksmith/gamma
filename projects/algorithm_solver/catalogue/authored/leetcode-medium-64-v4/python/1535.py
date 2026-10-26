"""1535. Find the Winner of an Array Game: track the current champion until its streak wins or it becomes the global maximum."""


def solve(arr: list[int], k: int) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    champion = arr[0]
    streak = 0
    for index in range(1, len(arr)):
        if champion > arr[index]:
            streak += 1
        else:
            champion = arr[index]
            streak = 1
        if streak >= k:
            return champion
    return champion


class Solution:
    def getWinner(self, arr: list[int], k: int) -> int:
        return solve(arr, k)
