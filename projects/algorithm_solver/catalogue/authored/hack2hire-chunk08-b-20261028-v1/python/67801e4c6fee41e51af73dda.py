"""Hack2Hire 67801e4c6fee41e51af73dda (Student Reading Textbook) over an INFERRED spec; qualification unknown."""

def solve(pages, days):
    if days < len(pages):
        return -1
    lo = max(1, -(-sum(pages) // days))
    hi = max(pages)
    while lo < hi:
        mid = (lo + hi) // 2
        if sum((p + mid - 1) // mid for p in pages) <= days:
            hi = mid
        else:
            lo = mid + 1
    return lo


class Solution:
    def minimumPagesPerDay(self, pages, days):
        return solve(pages, days)
