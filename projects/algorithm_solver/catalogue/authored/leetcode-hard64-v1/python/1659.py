"""1659. Maximize Grid Happiness: rolling ternary-frontier dynamic programming."""


def solve(m: int, n: int, introvertsCount: int, extrovertsCount: int) -> int:
    """O(m*n*3^w*(I+1)*(E+1)) time and O(3^w*(I+1)*(E+1)) space, w=min(m,n). Inputs are preserved."""
    width = min(m, n)
    cells = m * n
    introverts = min(introvertsCount, cells)
    extroverts = min(extrovertsCount, cells)
    profiles = 3 ** width
    upper_place = 3 ** (width - 1)
    extrovert_states = extroverts + 1
    interaction = ((0, 0, 0), (0, -60, -10), (0, -10, 40))
    states = {0: 0}
    for position in range(cells):
        following = {}
        for key, happiness in states.items():
            population, mask = divmod(key, profiles)
            used_introverts, used_extroverts = divmod(population, extrovert_states)
            upper = mask // upper_place
            left = mask % 3 if position % width else 0
            shifted = (mask % upper_place) * 3
            empty_key = population * profiles + shifted
            following[empty_key] = max(following.get(empty_key, -1), happiness)
            if used_introverts < introverts:
                next_key = (population + extrovert_states) * profiles + shifted + 1
                value = happiness + 120 + interaction[1][upper] + interaction[1][left]
                following[next_key] = max(following.get(next_key, -1), value)
            if used_extroverts < extroverts:
                next_key = (population + 1) * profiles + shifted + 2
                value = happiness + 40 + interaction[2][upper] + interaction[2][left]
                following[next_key] = max(following.get(next_key, -1), value)
        states = following
    return max(states.values())


class Solution:
    def getMaxGridHappiness(self, m: int, n: int, introvertsCount: int, extrovertsCount: int) -> int:
        return solve(m, n, introvertsCount, extrovertsCount)
