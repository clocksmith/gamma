"""Hack2Hire 6962cbcef731aa3969ef5176 (File System Deletion) over an INFERRED spec; qualification unknown."""


def solve(dirs, edges, files, path):
    directories = set(dirs)
    if path not in directories and path not in set(files):
        return []
    children = {}
    for parent, child in edges:
        children.setdefault(parent, []).append(child)
    deleted, stack, empty = [], [[path, 0]], ()
    while stack:
        top = stack[-1]
        kids = children.get(top[0], empty) if top[0] in directories else empty
        if top[1] < len(kids):
            stack.append([kids[top[1]], 0])
            top[1] += 1
        else:
            stack.pop()
            deleted.append(top[0])
    return deleted


class Solution:
    def deletePath(self, dirs, edges, files, path):
        return solve(dirs, edges, files, path)
