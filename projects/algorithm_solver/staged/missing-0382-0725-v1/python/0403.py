"""403. Frog Jump. Propagate feasible previous jump lengths to later stones."""

def solve(stones: list[int]) -> bool:
    jumps = {position: set() for position in stones}
    jumps[0].add(0)
    for position in stones:
        for jump in jumps[position]:
            for step in (jump - 1, jump, jump + 1):
                target = position + step
                if step > 0 and target in jumps:
                    jumps[target].add(step)
    return bool(jumps[stones[-1]])


class Solution:
    def canCross(self, stones: list[int]) -> bool:
        return solve(stones)
