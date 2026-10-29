"""Hack2Hire 67fbdd34216af53465a721a5 (Lowercase Before Uppercase Count) over an INFERRED spec; qualification unknown."""

def solve(s):
    last_lower, first_upper = {}, {}
    for i, ch in enumerate(s):
        if ch.islower():
            last_lower[ch] = i
        else:
            first_upper.setdefault(ch.lower(), i)
    count = 0
    for letter in set(last_lower) | set(first_upper):
        if letter not in last_lower or letter not in first_upper or last_lower[letter] < first_upper[letter]:
            count += 1
    return count


class Solution:
    def countLowerBeforeUpper(self, s):
        return solve(s)
