"""672. Bulb Switcher II. Enumerate button parity; the first three bulbs distinguish all reachable patterns."""

def solve(n: int, presses: int) -> int:
    size = min(n, 3)
    states = set()
    for mask in range(16):
        used = mask.bit_count()
        if used > presses or (presses - used) % 2:
            continue
        state = 0
        for position in range(1, size + 1):
            toggle = (mask & 1) != 0
            toggle ^= bool(mask & 2) and position % 2 == 0
            toggle ^= bool(mask & 4) and position % 2 == 1
            toggle ^= bool(mask & 8) and position % 3 == 1
            if not toggle:
                state |= 1 << (position - 1)
        states.add(state)
    return len(states)


class Solution:
    def flipLights(self, n: int, presses: int) -> int:
        return solve(n, presses)
