"""Original development candidate for frontend 3714; qualification pending."""

def solve(s):
    best = run = 0
    previous = None
    for char in s:
        run = run + 1 if char == previous else 1
        previous = char
        best = max(best, run)
    for first, second in [('a', 'b'), ('a', 'c'), ('b', 'c')]:
        difference = 0
        earliest = {0: -1}
        for i, char in enumerate(s):
            if char not in (first, second):
                difference = 0
                earliest = {0: i}
                continue
            difference += 1 if char == first else -1
            if difference in earliest:
                best = max(best, i - earliest[difference])
            else:
                earliest[difference] = i
    counts = [0, 0, 0]
    earliest = {(0, 0): -1}
    for i, char in enumerate(s):
        counts[ord(char) - 97] += 1
        key = (counts[0] - counts[1], counts[0] - counts[2])
        if key in earliest:
            best = max(best, i - earliest[key])
        else:
            earliest[key] = i
    return best


class Solution:
    def longestBalanced(self, s):
        return solve(s)
