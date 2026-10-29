"""Hack2Hire 67cd24763363b83a81fc99af (Check Password Similarity) over an INFERRED spec; qualification unknown."""


def similar(new, old):
    j, m = 0, len(old)
    for c in new:
        if j == m:
            break
        successor = 'a' if c == 'z' else chr(ord(c) + 1)
        if old[j] == c or old[j] == successor:
            j += 1
    return j == m


def solve(newPasswords, oldPasswords):
    return ['YES' if similar(new, old) else 'NO' for new, old in zip(newPasswords, oldPasswords)]


class Solution:
    def checkSimilarity(self, newPasswords, oldPasswords):
        return solve(newPasswords, oldPasswords)
