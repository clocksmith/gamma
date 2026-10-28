def solve(nums):
    previous = {}
    latest = {}
    answer = 0
    for r, x in enumerate(nums):
        current = {x: (r, r)}
        for value, (lo, hi) in previous.items():
            key = value | x
            if key in current:
                old_lo, old_hi = current[key]
                current[key] = (min(lo, old_lo), max(hi, old_hi))
            else:
                current[key] = (lo, hi)
        latest[x] = r
        for value, (lo, hi) in current.items():
            answer += max(0, min(hi, latest.get(value, -1)) - lo + 1)
        previous = current
    return answer


class Solution:
    def countGoodSubarrays(self, nums):
        return solve(nums)
