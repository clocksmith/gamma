"""Hack2Hire 6aa303f10ca9cc4e1c7901af (Directory Encryption Optimization, variant 1). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown."""


def solve(root):
    order, stack = [], [root]
    while stack:
        node = stack.pop()
        order.append(node)
        stack.extend(node['directories'])
    info = {}
    for node in reversed(order):
        cost, files, clean = 0, len(node['files']), True
        for f in node['files']:
            if f['isEncrypted']:
                cost += 1
            else:
                clean = False
        for child in node['directories']:
            child_cost, child_files, child_clean = info.pop(id(child))
            cost += child_cost
            files += child_files
            clean = clean and child_clean
        if files and clean:
            cost = 1
        info[id(node)] = (cost, files, clean)
    return info[id(root)][0]


class Solution:
    def minEncryptOperations(self, root):
        return solve(root)
