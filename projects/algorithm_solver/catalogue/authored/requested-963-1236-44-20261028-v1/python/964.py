"""Original candidate; no qualification or admission."""

def solve(x, target):
    digit=target%x;positive=2*digit;negative=2*(x-digit);target//=x;power=1
    while target:
        digit=target%x
        positive,negative=min(positive+digit*power,negative+(digit+1)*power),min(positive+(x-digit)*power,negative+(x-digit-1)*power)
        target//=x;power+=1
    return min(positive,negative+power)-1


class Solution:
    def leastOpsExpressTarget(self, x, target):
        return solve(x, target)
