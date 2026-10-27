# Original implementation. Contract: https://leetcode.com/problems/find-the-minimum-and-maximum-number-of-nodes-between-critical-points/
def solve(head_values):
    points=[i for i in range(1,len(head_values)-1) if (head_values[i]>head_values[i-1] and head_values[i]>head_values[i+1]) or (head_values[i]<head_values[i-1] and head_values[i]<head_values[i+1])]
    return [-1,-1] if len(points)<2 else [min(b-a for a,b in zip(points,points[1:])),points[-1]-points[0]]
