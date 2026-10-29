"""Original Hack2Hire 69c733a121f6ab4226966853 variant over an INFERRED specification; qualification unknown."""


def solve(nodes):
    out, stack = [], [0]
    while stack:
        row = nodes[stack.pop()]
        out.append([row[0], row[1]])
        stack.extend(reversed(row[2:]))
    return out


class Solution:
    def preorderTraversal(self, nodes):
        return solve(nodes)
