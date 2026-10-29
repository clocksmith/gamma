"""Hack2Hire 6a90b63acddc54478ddf423a (Largest Tree Root); INFERRED spec; qualification unknown."""


def solve(relations):
    if not relations: return -1
    children, is_child = {}, set()
    for child, parent in relations:
        children.setdefault(parent, []).append(child); is_child.add(child)
    best_root, best_size = -1, -1
    for root in children:
        if root in is_child: continue
        size, stack = 0, [root]
        while stack:
            node = stack.pop(); size += 1
            stack.extend(children.get(node, ()))
        if size > best_size or (size == best_size and root < best_root): best_root, best_size = root, size
    return best_root


class Solution:
    def largestTreeRoot(self, relations):
        return solve(relations)
