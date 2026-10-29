"""Original candidate; no qualification or admission."""

def solve(a,b):
    out=[]
    while a or b:
        choose_a=a>=b
        if len(out)>=2 and out[-1]==out[-2]:choose_a=out[-1]!='a'
        if choose_a:out.append('a');a-=1
        else:out.append('b');b-=1
    return ''.join(out)


class Solution:
    def strWithout3a3b(self, a, b):
        return solve(a, b)
