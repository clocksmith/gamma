# Original implementation. Contract: https://leetcode.com/problems/count-the-number-of-special-characters-ii/
def solve(word):
    last={};first={}
    for i,c in enumerate(word):
        if c.islower():last[c]=i
        elif c.lower() not in first:first[c.lower()]=i
    return sum(c in first and i<first[c] for c,i in last.items())
