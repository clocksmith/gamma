"""135. Candy."""
def solve(ratings: list[int]) -> int:
    candies = [1] * len(ratings)
    for index in range(1, len(ratings)):
        if ratings[index] > ratings[index - 1]:
            candies[index] = candies[index - 1] + 1
    total = candies[-1] if candies else 0
    for index in range(len(ratings) - 2, -1, -1):
        if ratings[index] > ratings[index + 1]:
            candies[index] = max(candies[index], candies[index + 1] + 1)
        total += candies[index]
    return total

class Solution:
    def candy(self, ratings: list[int]) -> int:
        return solve(ratings)
