def solve(s):
    # Odd total: remove all. Positive even total: leave an odd total for Bob.
    return any(c in "aeiou" for c in s)
