"""2517. Maximum Tastiness of Candy Basket: binary search the minimum separation with an earliest-feasible greedy selection."""


def solve(price: list[int], k: int) -> int:
    """O(n log n + n log(M + 1)) time and O(n) auxiliary space, where M is the price range; inputs are read-only."""
    ordered = sorted(price)
    low, high = 0, (ordered[-1] - ordered[0]) // (k - 1)
    while low < high:
        gap = (low + high + 1) // 2
        selected = 1
        last = ordered[0]
        for value in ordered[1:]:
            if value - last >= gap:
                selected += 1
                last = value
                if selected == k:
                    break
        if selected >= k:
            low = gap
        else:
            high = gap - 1
    return low


class Solution:
    def maximumTastiness(self, price: list[int], k: int) -> int:
        return solve(price, k)
