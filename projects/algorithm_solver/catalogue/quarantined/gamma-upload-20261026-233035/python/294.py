"""294. Flip Game II."""
from functools import lru_cache

def solve(currentState: str) -> bool:
    @lru_cache(None)
    def win(state: str) -> bool:
        for index in range(len(state) - 1):
            if state[index:index + 2] == '++':
                following = state[:index] + '--' + state[index + 2:]
                if not win(following):
                    return True
        return False
    return win(currentState)

class Solution:
    def canWin(self, currentState: str) -> bool:
        return solve(currentState)
