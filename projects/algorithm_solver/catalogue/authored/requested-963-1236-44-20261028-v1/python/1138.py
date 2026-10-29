"""Original candidate; no qualification or admission."""

def solve(target):
    r=c=0;out=[]
    for letter in target:
        nr,nc=divmod(ord(letter)-97,5)
        out.extend(['U'*max(0,r-nr),'L'*max(0,c-nc),'D'*max(0,nr-r),'R'*max(0,nc-c),'!']);r,c=nr,nc
    return ''.join(out)


class Solution:
    def alphabetBoardPath(self, target):
        return solve(target)
