"""1563. Stone Game V: monotone split boundaries and interval maxima for positive stones; O(n^2) time and space."""


def solve(stoneValue: list[int]) -> int:
    size = len(stoneValue)
    prefix = [0]
    for value in stoneValue:
        prefix.append(prefix[-1] + value)
    left_best = [[0] * size for _ in range(size)]
    right_best = [[0] * size for _ in range(size)]
    answer = 0
    for left in range(size - 1, -1, -1):
        left_best[left][left] = right_best[left][left] = stoneValue[left]
        split = left - 1
        for right in range(left + 1, size):
            total = prefix[right + 1] - prefix[left]
            while split + 1 < right and 2 * (prefix[split + 2] - prefix[left]) <= total:
                split += 1
            best = left_best[left][split] if split >= left else 0
            equal = split >= left and 2 * (prefix[split + 1] - prefix[left]) == total
            right_start = split + 1 if equal else split + 2
            if right_start <= right:
                best = max(best, right_best[right_start][right])
            left_best[left][right] = max(left_best[left][right - 1], total + best)
            right_best[left][right] = max(right_best[left + 1][right], total + best)
            if left == 0 and right == size - 1:
                answer = best
    return answer


class Solution:
    def stoneGameV(self, stoneValue: list[int]) -> int:
        return solve(stoneValue)
