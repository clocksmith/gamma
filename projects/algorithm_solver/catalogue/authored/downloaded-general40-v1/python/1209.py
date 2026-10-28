"""1209. Remove All Adjacent Duplicates in String II (Medium).

Specification: https://leetcode.com/problems/remove-all-adjacent-duplicates-in-string-ii/description/
"""


def solve(s: str, k: int) -> str:
    stack = []
    for ch in s:
        if stack and stack[-1][0] == ch:
            stack[-1][1] += 1
        else:
            stack.append([ch, 1])
        if stack[-1][1] == k:
            stack.pop()
    return "".join(ch * count for ch, count in stack)


class Solution:
    def removeDuplicates(self, s: str, k: int) -> str:
        return solve(s, k)
