# Original candidate implementation. Contract: https://leetcode.com/problems/match-substring-after-replacement/
def solve(s,sub,mappings):
    allowed=set(map(tuple,mappings))
    for i in range(len(s)-len(sub)+1):
        if all(a==b or (a,b) in allowed for a,b in zip(sub,s[i:i+len(sub)])):return True
    return False
