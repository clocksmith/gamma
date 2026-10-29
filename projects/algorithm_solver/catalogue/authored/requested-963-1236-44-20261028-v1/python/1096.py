"""Original candidate; no qualification or admission."""

def solve(expression):
    at=0
    def union():
        nonlocal at
        result=concatenation()
        while at<len(expression) and expression[at]==',':at+=1;result|=concatenation()
        return result
    def concatenation():
        nonlocal at
        result={''}
        while at<len(expression) and expression[at] not in '},':
            if expression[at]=='{':at+=1;part=union();at+=1
            else:part={expression[at]};at+=1
            result={a+b for a in result for b in part}
        return result
    return sorted(union())


class Solution:
    def braceExpansionII(self, expression):
        return solve(expression)
