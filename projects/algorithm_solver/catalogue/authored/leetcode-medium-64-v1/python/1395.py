"""1395. Count Number of Teams: count smaller and larger choices around each middle soldier."""


def solve(rating: list[int]) -> int:
    """O(n^2) time and O(1) auxiliary space; inputs are read-only."""
    answer = 0
    for middle, value in enumerate(rating):
        left_smaller = left_larger = 0
        right_smaller = right_larger = 0
        for left in range(middle):
            left_smaller += rating[left] < value
            left_larger += rating[left] > value
        for right in range(middle + 1, len(rating)):
            right_smaller += rating[right] < value
            right_larger += rating[right] > value
        answer += left_smaller * right_larger + left_larger * right_smaller
    return answer


class Solution:
    def numTeams(self, rating: list[int]) -> int:
        return solve(rating)
