"""Original candidate for LeetCode 2375. Contract: https://leetcode.com/problems/construct-smallest-number-from-di-string/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n) time and space"""
def solve(pattern):
    out=[];stack=[]
    for i in range(len(pattern)+1):
        stack.append(str(i+1))
        if i==len(pattern) or pattern[i]=='I':
            out.extend(reversed(stack));stack.clear()
    return ''.join(out)
