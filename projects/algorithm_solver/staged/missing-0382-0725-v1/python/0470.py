"""470. Implement Rand10() Using Rand7()."""

def solve(rand7_api=None) -> int:
    """The host supplies rand7() or passes it explicitly; rejection sampling is unbiased."""
    draw = rand7 if rand7_api is None else rand7_api
    while True:
        value = (draw() - 1) * 7 + draw() - 1
        if value < 40:
            return value % 10 + 1


class Solution:
    def rand10(self) -> int:
        return solve()
