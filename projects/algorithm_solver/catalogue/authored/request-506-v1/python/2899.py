"""Original candidate for LeetCode 2899. Contract: https://leetcode.com/problems/last-visited-integers/
Development tests only; not admitted or independently qualified.
Current official contract takes positive integers and -1, not historical string words.
Complexity: O(n) time and space"""
def solve(nums):
    seen=[];ans=[];k=0
    for x in nums:
        if x==-1:
            k+=1;ans.append(seen[-k] if k<=len(seen) else -1)
        else:seen.append(x);k=0
    return ans
