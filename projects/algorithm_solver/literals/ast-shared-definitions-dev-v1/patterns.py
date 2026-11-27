"""Linear, typed A2 patterns shared by both library selectors.

Every hole is filled once, at the same syntax position from which its argument
was taken. Expansion restores the original declaration/reference order, including
when a hole contains another invocation. No term is moved across a binder.
"""

from functools import lru_cache
from pathlib import Path
import sys

A2 = Path(__file__).resolve().parent.parent / "a2-recursive-frames-v1"
if str(A2) not in sys.path:
    sys.path.append(str(A2))
import ast_frames as a2

MAX_NODES = 12
MAX_HOLES = 4


def to_wire(node):
    """Strip transient IDs and source pointers while preserving every IR atom."""
    return ("NODE", node.group, node.tag, node.atoms, tuple(map(to_wire, node.children)))


@lru_cache(maxsize=2048)
def _slots(group, tag, atoms):
    if group == "EXPR" and tag in a2.SIMPLE_EXPR_TAGS:
        return tuple(a2.child_contexts_of_frame_node(group, tag, atoms))
    if group == "STMT" and tag in a2.SIMPLE_STMT_TAGS:
        if tag == "VarDecl" and not atoms[2]:
            return None
        if tag == "Block" and atoms[0] > 3:
            return None
        return tuple(a2.child_contexts_of_frame_node(group, tag, atoms))
    return None


def _node_slots(node):
    slots = _slots(node[1], node[2], node[3])
    if slots is None or len(slots) != len(node[4]):
        return None
    return slots


def _cut(node, slot, depth):
    """Keep a bounded, frameable prefix; preserve other children at typed holes."""
    if depth == 0 or (slots := _node_slots(node)) is None:
        return ("HOLE", *slot)
    return (*node[:4], tuple(_cut(c, s, depth - 1) for c, s in zip(node[4], slots)))


def _size(tree):
    if tree[0] == "HOLE":
        return 0, 1
    sizes = [_size(child) for child in tree[4]]
    return 1 + sum(n for n, _ in sizes), sum(h for _, h in sizes)


@lru_cache(maxsize=8192)
def _canonical(tree):
    return a2.tpl_canonicalize_shift_exact(tree, {})[0]


def templates(node):
    """Enumerate the same bounded open and closed structures for both trainers."""
    slots = _node_slots(node)
    if slots is None or not slots:
        return
    holes = tuple(("HOLE", *slot) for slot in slots)
    seen = set()
    for depth in (0, 1, 2):
        children = tuple(_cut(c, s, depth) for c, s in zip(node[4], slots))
        variants = [children]
        if depth and len(slots) > 1:
            variants.extend((*holes[:i], child, *holes[i + 1:]) for i, child in enumerate(children))
        for variant in variants:
            candidate = (*node[:4], variant)
            size, arity = _size(candidate)
            if size <= MAX_NODES and arity <= MAX_HOLES:
                pattern = _canonical(candidate)
                if pattern not in seen:
                    seen.add(pattern)
                    yield pattern


def match(template, node):
    """Return the unique Reg8 shift and site-ordered arguments, or None.

    One Reg8 literal fixes the shift modulo eight. Every further Reg8 must agree.
    RegFar and FreeId are literal tag/atom matches and never participate.
    """
    if template[0] != "NODE":
        return None
    shift = None
    args = []

    def visit(pattern, target, slot):
        nonlocal shift
        if pattern[0] == "HOLE":
            if pattern[1:] != slot or target[1] != slot[0]:
                return False
            args.append(target)
            return True
        if pattern[:3] != target[:3]:
            return False
        if pattern[2] == "Reg8":
            wanted, actual = pattern[3], target[3]
            if (len(wanted) != 1 or len(actual) != 1 or wanted[0] not in range(8)
                    or actual[0] not in range(8) or pattern[4] or target[4]):
                return False
            delta = (actual[0] - wanted[0]) % 8
            if shift is None:
                shift = delta
            return shift == delta
        if pattern[3] != target[3] or len(pattern[4]) != len(target[4]):
            return False
        slots = _node_slots(target)
        return slots is not None and all(
            visit(p, child, role) for p, child, role in zip(pattern[4], target[4], slots)
        )

    if visit(template, node, None):
        return (shift or 0), tuple(args)
    return None
