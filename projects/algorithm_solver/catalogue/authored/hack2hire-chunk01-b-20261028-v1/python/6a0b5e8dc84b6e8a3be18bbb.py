"""Hack2Hire 6a0b5e8dc84b6e8a3be18bbb (Find Camera Admin User). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown."""
from collections import deque


def solve(permissions, cameraId):
    holders, users = {}, set()
    for entity, relation, target in permissions:
        holders.setdefault(target, []).append(entity)
        if relation == 'cameraOwner' or relation == 'groupMember':
            users.add(entity)
    seen, queue = {cameraId}, deque([cameraId])
    while queue:
        current = queue.popleft()
        for entity in holders.get(current, ()):
            if entity not in seen:
                seen.add(entity)
                queue.append(entity)
    return sorted(x for x in seen if x in users)


class Solution:
    def findCameraAdmins(self, permissions, cameraId):
        return solve(permissions, cameraId)
