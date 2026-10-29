"""Hack2Hire 696442bb3b4797da7459a055 (File System Directory Size Sum) over an INFERRED spec; qualification unknown."""


def solve(root, limit):
    answer = 0
    stack = [[root['children'], 0, 0]]  # [children, next index, running total]
    while stack:
        frame = stack[-1]
        kids = frame[0]
        if frame[1] < len(kids):
            child = kids[frame[1]]
            frame[1] += 1
            if 'children' in child:
                stack.append([child['children'], 0, 0])
            else:
                frame[2] += child['size']
        else:
            stack.pop()
            total = frame[2]
            if total <= limit:
                answer += total
            if stack:
                stack[-1][2] += total
    return answer


class Solution:
    def sumDirectorySizes(self, root, limit):
        return solve(root, limit)
