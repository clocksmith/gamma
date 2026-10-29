"""Original Hack2Hire 69c7438121f6ab4226966890 variant over an INFERRED specification; qualification unknown."""


def solve(nodesA, nodesB):
    out, stack = [], [(0, 0, -1)]
    while stack:
        a, b, parent = stack.pop()
        source = nodesA[a] if a is not None else nodesB[b]
        value = (nodesA[a][1] if a is not None else 0) + (nodesB[b][1] if b is not None else 0)
        index = len(out)
        out.append([source[0], value])
        if parent >= 0:
            out[parent].append(index)
        b_by_key = {nodesB[c][0]: c for c in nodesB[b][2:]} if b is not None else {}
        pairs = []
        if a is not None:
            for c in nodesA[a][2:]:
                pairs.append((c, b_by_key.pop(nodesA[c][0], None)))
        if b is not None:
            for c in nodesB[b][2:]:
                if nodesB[c][0] in b_by_key:
                    pairs.append((None, c))
        for child_a, child_b in reversed(pairs):
            stack.append((child_a, child_b, index))
    return out


class Solution:
    def mergeTrees(self, nodesA, nodesB):
        return solve(nodesA, nodesB)
