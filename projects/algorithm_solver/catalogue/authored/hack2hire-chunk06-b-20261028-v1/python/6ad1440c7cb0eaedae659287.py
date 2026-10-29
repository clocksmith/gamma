"""Hack2Hire 6ad1440c7cb0eaedae659287 (Format a Task Hierarchy, level 4) over an INFERRED spec; qualification unknown."""

LEVEL = 4


def solve(records):
    arity = {'task': 4, 'subtask': 5}
    if LEVEL == 4:
        arity['complete'] = 3
    parent_of, name_of, order, marked = {}, {}, [], set()
    for record in records:
        fields = record.split(',')
        if len(fields) < 2 or arity.get(fields[1]) != len(fields):
            continue
        if fields[1] == 'complete':
            if fields[2]:
                marked.add(fields[2])
            continue
        if fields[1] == 'task':
            parent, task_id, name = None, fields[2], fields[3]
        else:
            parent, task_id, name = fields[2], fields[3], fields[4]
        if not task_id or not name or parent == '' or task_id in name_of:
            continue
        parent_of[task_id], name_of[task_id] = parent, name
        order.append(task_id)
    children, roots = {}, []
    for task_id in order:
        parent = parent_of[task_id]
        if parent is None:
            roots.append(task_id)
        else:
            children.setdefault(parent, []).append(task_id)
    # pre-order walk of everything reachable from the roots (orphans and cycles are never reached)
    visit, stack = [], [(roots[i], 0, str(i + 1)) for i in range(len(roots) - 1, -1, -1)]
    while stack:
        task_id, depth, number = stack.pop()
        visit.append((task_id, depth, number))
        kids = children.get(task_id, [])
        for j in range(len(kids) - 1, -1, -1):
            stack.append((kids[j], depth + 1, number + '.' + str(j + 1)))
    done = {}
    if LEVEL == 4:
        for task_id, _, _ in reversed(visit):
            kids = children.get(task_id, [])
            done[task_id] = task_id in marked or (len(kids) > 0 and all(done[k] for k in kids))
    lines = []
    for task_id, depth, number in visit:
        label = name_of[task_id]
        if LEVEL == 4:
            label = ('[x] ' if done[task_id] else '[ ] ') + label
        if LEVEL >= 3:
            label = number + ' ' + label
        lines.append('  ' * depth + label)
    return lines


class Solution:
    def formatTasks(self, records):
        return solve(records)
