"""Original candidate for LeetCode 2957. Contract: https://leetcode.com/problems/remove-adjacent-almost-equal-characters/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n) time, O(1) space"""
def solve(word):
    i=1;ans=0
    while i<len(word):
        if abs(ord(word[i])-ord(word[i-1]))<=1:ans+=1;i+=2
        else:i+=1
    return ans
