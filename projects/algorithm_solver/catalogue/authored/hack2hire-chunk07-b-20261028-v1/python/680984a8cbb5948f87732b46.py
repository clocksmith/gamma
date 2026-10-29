"""Hack2Hire 680984a8cbb5948f87732b46 (Nested Set Equality) over an INFERRED spec; qualification unknown."""

def solve(a, b):
    ids = {}

    def canonical(root):
        frames = [[root, 0, []]]
        while True:
            frame = frames[-1]
            node, i, acc = frame
            if i < len(node):
                frame[1] = i + 1
                x = node[i]
                if type(x) is str:
                    acc.append(ids.setdefault(('atom', x), len(ids)))
                else:
                    frames.append([x, 0, []])
            else:
                key = ('set', tuple(sorted(set(acc))))
                lid = ids.setdefault(key, len(ids))
                frames.pop()
                if not frames:
                    return lid
                frames[-1][2].append(lid)

    return canonical(a) == canonical(b)


class Solution:
    def nestedSetEqual(self, a, b):
        return solve(a, b)
