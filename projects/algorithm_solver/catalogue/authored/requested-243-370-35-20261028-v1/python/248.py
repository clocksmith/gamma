"""Original frontend 248 variant; qualification unknown."""


def solve(low: str, high: str) -> int:
    pairs = (("0", "0"), ("1", "1"), ("6", "9"), ("8", "8"), ("9", "6"))
    ln_lo, ln_hi = len(low), len(high)
    count = 0
    for length in range(ln_lo, ln_hi + 1):
        cur = [""] if length % 2 == 0 else ["0", "1", "8"]
        rem = length - (length % 2)
        while rem > 0:
            is_outer = rem == 2
            nxt = []
            for s in cur:
                for a, b in pairs:
                    if is_outer and length > 1 and a == "0":
                        continue
                    nxt.append(a + s + b)
            cur = nxt
            rem -= 2
        for s in cur:
            if (len(s) > ln_lo or s >= low) and (len(s) < ln_hi or s <= high):
                count += 1
    return count


strobogrammaticInRange = solve


class Solution:
    def strobogrammaticInRange(self, low: str, high: str) -> int:
        return solve(low, high)
