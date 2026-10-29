"""Original Hack2Hire 6941d017e79fe20cf9ff443f variant over an INFERRED specification; qualification unknown."""


def solve(relationships):
    children, reports = {}, set()
    for row in relationships:
        children[row[0]] = row[1:]
        reports.update(row[1:])
    root = next(row[0] for row in relationships if row[0] not in reports)
    lines, stack = [], [(root, 0)]
    while stack:
        name, depth = stack.pop()
        lines.append('  ' * depth + name)
        for child in reversed(children.get(name, ())):
            stack.append((child, depth + 1))
    return lines


class Solution:
    def printHierarchy(self, relationships):
        return solve(relationships)
