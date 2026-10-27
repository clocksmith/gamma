"""248. Strobogrammatic Number III."""
def solve(low: str, high: str) -> int:
    pairs = [('0', '0'), ('1', '1'), ('6', '9'), ('8', '8'), ('9', '6')]
    total = 0
    def build(chars: list[str], left: int, right: int) -> None:
        nonlocal total
        if left > right:
            value = ''.join(chars)
            if (len(value) == len(low) and value < low) or (len(value) == len(high) and value > high):
                return
            total += 1
            return
        for a, b in pairs:
            if left == 0 and len(chars) > 1 and a == '0':
                continue
            if left == right and a != b:
                continue
            chars[left], chars[right] = a, b
            build(chars, left + 1, right - 1)
    for length in range(len(low), len(high) + 1):
        build([''] * length, 0, length - 1)
    return total

class Solution:
    def strobogrammaticInRange(self, low: str, high: str) -> int:
        return solve(low, high)
