"""Original candidate for LeetCode 2730. Contract: https://leetcode.com/problems/find-the-longest-semi-repetitive-substring/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n) time, O(1) space"""
def solve(s):
    left=0;pairs=0;ans=0
    for right in range(len(s)):
        if right and s[right]==s[right-1]:pairs+=1
        while pairs>1:
            if s[left]==s[left+1]:pairs-=1
            left+=1
        ans=max(ans,right-left+1)
    return ans
