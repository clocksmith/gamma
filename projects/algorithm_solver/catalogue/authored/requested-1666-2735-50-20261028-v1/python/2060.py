"""Original candidate; no qualification or admission."""

from functools import lru_cache

def solve(s1,s2):
    @lru_cache(None)
    def visit(i,j,difference):
        if i==len(s1) and j==len(s2):return difference==0
        if i<len(s1) and s1[i].isdigit():
            value=0
            for end in range(i,min(i+3,len(s1))):
                if not s1[end].isdigit():break
                value=value*10+int(s1[end])
                if visit(end+1,j,difference+value):return True
        if j<len(s2) and s2[j].isdigit():
            value=0
            for end in range(j,min(j+3,len(s2))):
                if not s2[end].isdigit():break
                value=value*10+int(s2[end])
                if visit(i,end+1,difference-value):return True
        if difference>0 and j<len(s2) and s2[j].isalpha() and visit(i,j+1,difference-1):return True
        if difference<0 and i<len(s1) and s1[i].isalpha() and visit(i+1,j,difference+1):return True
        return difference==0 and i<len(s1) and j<len(s2) and s1[i].isalpha() and s1[i]==s2[j] and visit(i+1,j+1,0)
    return visit(0,0,0)


class Solution:
    def possiblyEquals(self, s1, s2):
        return solve(s1, s2)
