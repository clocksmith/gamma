"""2111. Minimum Operations to Make the Array K-Increasing."""

from bisect import bisect_right


def solve(arr: list[int], k: int) -> int:
    """O(n*log(1+n/k)) time, O(ceil(n/k)) space; solve each residue class independently."""
    answer = 0
    for start in range(k):
        tails = []
        count = 0
        for index in range(start, len(arr), k):
            value = arr[index]
            slot = bisect_right(tails, value)
            if slot == len(tails):
                tails.append(value)
            else:
                tails[slot] = value
            count += 1
        answer += count - len(tails)
    return answer


class Solution:
    def kIncreasing(self, arr: list[int], k: int) -> int:
        return solve(arr, k)
