"""Hack2Hire 67fd5bf3d2adf72ba62b0ecc (Jaccard Business Similarity) over an INFERRED spec; qualification unknown."""


def solve(s1, s2):
    a = set(s1.split(' ')) if s1 else set()
    b = set(s2.split(' ')) if s2 else set()
    if not a and not b:
        return 1.0
    common = 0
    for word in a:
        if word in b:
            common += 1
    union = len(a) + len(b) - common
    hundredths = (200 * common + union) // (2 * union)
    return hundredths / 100


class Solution:
    def jaccardSimilarity(self, s1, s2):
        return solve(s1, s2)
