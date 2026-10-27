# Original implementation. Contract: https://leetcode.com/problems/find-the-number-of-distinct-colors-among-the-balls/
from collections import Counter
def solve(limit,queries):
    balls={};counts=Counter();out=[]
    for ball,color in queries:
        if ball in balls:
            old=balls[ball];counts[old]-=1
            if not counts[old]:del counts[old]
        balls[ball]=color;counts[color]+=1;out.append(len(counts))
    return out
