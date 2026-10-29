"""Original Hack2Hire 6945a3fbe85c245612a9786c variant over an INFERRED specification; qualification unknown."""


def solve(relationships):
    children, reports = {}, set()
    for row in relationships:
        children[row[0]] = row[1:]
        reports.update(row[1:])
    root = next(row[0] for row in relationships if row[0] not in reports)
    order, parent, stack = [], {root: None}, [(root, 0)]
    while stack:
        name, depth = stack.pop()
        order.append((name, depth))
        for child in reversed(children.get(name, ())):
            parent[child] = name
            stack.append((child, depth + 1))
    below = {name: 0 for name, _ in order}
    for name, _ in reversed(order):
        if parent[name] is not None:
            below[parent[name]] += below[name] + 1
    return ['  ' * depth + name + ' (' + str(below[name]) + ')' for name, depth in order]


class Solution:
    def printHierarchyWithCounts(self, relationships):
        return solve(relationships)
