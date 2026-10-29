"""Hack2Hire 68e8736a80f69c7a01706891 (Print Folder Path Given Node ID) over an INFERRED spec; qualification unknown."""


def solve(idList, children, nameList, targetId):
    name = {}
    for i, n in zip(idList, nameList):
        name[i] = n
    if targetId not in name:
        return ''
    parent = {}
    for i, kids in zip(idList, children):
        for k in kids:
            parent[k] = i
    path = []
    node = targetId
    while True:
        path.append(name[node])
        if node not in parent:
            break
        node = parent[node]
    path.reverse()
    return '/'.join(path)


class Solution:
    def getFolderPath(self, idList, children, nameList, targetId):
        return solve(idList, children, nameList, targetId)
