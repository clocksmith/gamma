"""2528. Maximize the Minimum Powered City. Binary search the minimum power with rightmost greedy placements."""


def solve(stations: list[int], r: int, k: int) -> int:
    """O(n log(k+2)) time and O(n) space. Inputs are preserved."""
    size = len(stations)
    prefix = [0]
    for value in stations:
        prefix.append(prefix[-1] + value)
    power = [prefix[min(size, index + r + 1)] - prefix[max(0, index - r)] for index in range(size)]

    def feasible(target):
        changes = [0] * (size + 1)
        active = used = 0
        for index in range(size):
            active += changes[index]
            missing = target - power[index] - active
            if missing <= 0:
                continue
            used += missing
            if used > k:
                return False
            active += missing
            changes[min(size, index + 2 * r + 1)] -= missing
        return True

    low = min(power)
    high = low + k
    while low < high:
        middle = (low + high + 1) // 2
        if feasible(middle):
            low = middle
        else:
            high = middle - 1
    return low


class Solution:
    def maxPower(self, stations: list[int], r: int, k: int) -> int:
        return solve(stations, r, k)
