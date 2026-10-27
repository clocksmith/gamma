"""473. Matchsticks to Square."""

def solve(matchsticks: list[int]) -> bool:
    total = sum(matchsticks)
    if len(matchsticks) < 4 or total % 4:
        return False
    target = total // 4
    sticks = sorted(matchsticks, reverse=True)
    if sticks[0] > target:
        return False
    sides = [0] * 4
    def place(index):
        if index == len(sticks):
            return True
        tried = set()
        for side in range(4):
            before = sides[side]
            if before in tried or before + sticks[index] > target:
                continue
            tried.add(before)
            sides[side] += sticks[index]
            if place(index + 1):
                return True
            sides[side] = before
        return False
    return place(0)


class Solution:
    def makesquare(self, matchsticks: list[int]) -> bool:
        return solve(matchsticks)
