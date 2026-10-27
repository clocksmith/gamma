"""Original candidate for LeetCode 3111. Contract: https://leetcode.com/problems/minimum-rectangles-to-cover-points/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n log n) time, O(n) space"""
def solve(points,w):
    end=-1;ans=0
    for x in sorted(p[0] for p in points):
        if x>end:ans+=1;end=x+w
    return ans
