"""1276. Number of Burgers with No Waste of Ingredients: solve the two ingredient equations with nonnegative integer counts."""


def solve(tomatoSlices: int, cheeseSlices: int) -> list[int]:
    """O(1) time and O(1) auxiliary space; inputs are read-only."""
    extra = tomatoSlices - 2 * cheeseSlices
    if extra < 0 or extra % 2 != 0 or extra > 2 * cheeseSlices:
        return []
    jumbo = extra // 2
    return [jumbo, cheeseSlices - jumbo]


class Solution:
    def numOfBurgers(self, tomatoSlices: int, cheeseSlices: int) -> list[int]:
        return solve(tomatoSlices, cheeseSlices)
