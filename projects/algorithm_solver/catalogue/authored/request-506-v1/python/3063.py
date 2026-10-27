# Original candidate. Contract: https://leetcode.com/problems/linked-list-frequency/
def solve(head):
    from collections import Counter
    return list(Counter(head).values())
