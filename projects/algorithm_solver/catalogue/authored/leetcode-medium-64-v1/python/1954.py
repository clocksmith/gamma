"""1954. Minimum Garden Perimeter to Collect Enough Apples: binary search the square radius using the exact apple-count polynomial."""


def solve(neededApples: int) -> int:
    """O(log(neededApples + 1)) time and O(1) auxiliary space on the bounded integer domain; inputs are read-only."""
    def apples(radius: int) -> int:
        return 2 * radius * (radius + 1) * (2 * radius + 1)

    low = high = 1
    while apples(high) < neededApples:
        high *= 2
    while low < high:
        middle = (low + high) // 2
        if apples(middle) >= neededApples:
            high = middle
        else:
            low = middle + 1
    return 8 * low


class Solution:
    def minimumPerimeter(self, neededApples: int) -> int:
        return solve(neededApples)
