"""Original candidate; no qualification or admission."""

def solve(text):
    left=right='';answer=0;l=0;r=len(text)-1
    while l<=r:
        left+=text[l];right=text[r]+right
        if left==right:answer+=1 if l==r else 2;left=right=''
        l+=1;r-=1
    return answer+(1 if left else 0)


class Solution:
    def longestDecomposition(self, text):
        return solve(text)
