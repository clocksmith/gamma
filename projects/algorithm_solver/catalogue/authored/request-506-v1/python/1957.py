# Original implementation. Contract: https://leetcode.com/problems/delete-characters-to-make-fancy-string/
def solve(s):
    out=[]
    for c in s:
        if len(out)<2 or out[-1]!=c or out[-2]!=c: out.append(c)
    return ''.join(out)
