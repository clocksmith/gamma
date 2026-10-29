"""Original frontend 558 variant; qualification unknown."""
from collections import deque


class Node:
    def __init__(self, val, isLeaf, topLeft=None, topRight=None, bottomLeft=None, bottomRight=None):
        self.val = bool(val)
        self.isLeaf = bool(isLeaf)
        self.topLeft = topLeft
        self.topRight = topRight
        self.bottomLeft = bottomLeft
        self.bottomRight = bottomRight


def _from_quad_list(data):
    root = Node(bool(data[0][1]), bool(data[0][0]))
    q = deque([root])
    i = 1
    while q and i < len(data):
        curr = q.popleft()
        for attr in ("topLeft", "topRight", "bottomLeft", "bottomRight"):
            if i < len(data):
                item = data[i]
                i += 1
                if item is not None:
                    child = Node(bool(item[1]), bool(item[0]))
                    setattr(curr, attr, child)
                    q.append(child)
    return root


def _to_quad_list(root):
    out = []
    q = deque([root])
    while q:
        node = q.popleft()
        if node is None:
            out.append(None)
        else:
            out.append([1 if node.isLeaf else 0, 1 if node.val else 0])
            q.append(node.topLeft)
            q.append(node.topRight)
            q.append(node.bottomLeft)
            q.append(node.bottomRight)
    while out and out[-1] is None:
        out.pop()
    return out


def _intersect_nodes(q1: Node, q2: Node) -> Node:
    if q1.isLeaf:
        return Node(True, True) if q1.val else q2
    if q2.isLeaf:
        return Node(True, True) if q2.val else q1
    tl = _intersect_nodes(q1.topLeft, q2.topLeft)
    tr = _intersect_nodes(q1.topRight, q2.topRight)
    bl = _intersect_nodes(q1.bottomLeft, q2.bottomLeft)
    br = _intersect_nodes(q1.bottomRight, q2.bottomRight)
    if tl.isLeaf and tr.isLeaf and bl.isLeaf and br.isLeaf and tl.val == tr.val == bl.val == br.val:
        return Node(tl.val, True)
    return Node(True, False, tl, tr, bl, br)


def solve(quadTree1, quadTree2):
    if isinstance(quadTree1, list):
        n1 = _from_quad_list(quadTree1)
        n2 = _from_quad_list(quadTree2)
        return _to_quad_list(_intersect_nodes(n1, n2))
    return _intersect_nodes(quadTree1, quadTree2)


intersect = solve


class Solution:
    def intersect(self, quadTree1, quadTree2):
        return solve(quadTree1, quadTree2)
