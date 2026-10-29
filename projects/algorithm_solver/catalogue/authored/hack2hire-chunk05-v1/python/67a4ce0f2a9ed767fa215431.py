"""Original hack2hire:67a4ce0f2a9ed767fa215431; inferred public-preview contract; qualification unknown."""
def countDistinctPasswords(password):
    seen = 0
    counts = {}
    result = 1
    for ch in password:
        result += seen - counts.get(ch, 0)
        counts[ch] = counts.get(ch, 0) + 1
        seen += 1
    return result

solve = countDistinctPasswords

class Solution:
    countDistinctPasswords = staticmethod(countDistinctPasswords)
