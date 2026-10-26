"""2611. Mice and Cheese: start with the second mouse rewards and take the k largest reassignment gains."""


def solve(reward1: list[int], reward2: list[int], k: int) -> int:
    """O(n log n) time and O(n) auxiliary space; inputs are read-only."""
    gains = sorted((first - second for first, second in zip(reward1, reward2)), reverse=True)
    answer = sum(reward2)
    for index in range(k):
        answer += gains[index]
    return answer


class Solution:
    def miceAndCheese(self, reward1: list[int], reward2: list[int], k: int) -> int:
        return solve(reward1, reward2, k)
