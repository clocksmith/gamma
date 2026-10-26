"""1333. Filter Restaurants by Vegan-Friendly, Price and Distance: filter eligible records then sort by descending rating and identifier."""


def solve(restaurants: list[list[int]], veganFriendly: int, maxPrice: int, maxDistance: int) -> list[int]:
    """O(n log n) time and O(n) auxiliary space; inputs are read-only."""
    eligible = [(rating, identifier) for identifier, rating, vegan, price, distance in restaurants
                if (not veganFriendly or vegan == 1) and price <= maxPrice and distance <= maxDistance]
    eligible.sort(reverse=True)
    return [identifier for _, identifier in eligible]


class Solution:
    def filterRestaurants(self, restaurants: list[list[int]], veganFriendly: int, maxPrice: int, maxDistance: int) -> list[int]:
        return solve(restaurants, veganFriendly, maxPrice, maxDistance)
