"""Hack2Hire 6801c3b66cd5d6c88778f20c (Role Privilege System) over an INFERRED spec; qualification unknown."""


def solve(roles, parents, allowed, disallowed):
    n = len(roles)
    position = {role: i for i, role in enumerate(roles)}
    children = [[] for _ in range(n)]
    waiting = [len(p) for p in parents]
    for i, role_parents in enumerate(parents):
        for parent in role_parents:
            children[position[parent]].append(i)
    final = [None] * n
    queue = [i for i in range(n) if waiting[i] == 0]
    head = 0
    while head < len(queue):
        i = queue[head]
        head += 1
        privileges = set(allowed[i])
        for parent in parents[i]:
            privileges.update(final[position[parent]])
        privileges.difference_update(disallowed[i])
        final[i] = privileges
        for child in children[i]:
            waiting[child] -= 1
            if waiting[child] == 0:
                queue.append(child)
    return [sorted(p) for p in final]


class Solution:
    def finalPrivileges(self, roles, parents, allowed, disallowed):
        return solve(roles, parents, allowed, disallowed)
