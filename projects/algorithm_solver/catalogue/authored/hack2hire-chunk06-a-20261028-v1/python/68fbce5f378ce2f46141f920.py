"""Hack2Hire 68fbce5f378ce2f46141f920 (File System Collection) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class FileSystemStats:
    def __init__(self, files):
        self.total = 0
        self.direct = {}
        for record in files:
            parts = record.split(',')
            size = int(parts[1])
            self.total += size
            for collection in set(parts[2:]):
                self.direct[collection] = self.direct.get(collection, 0) + size
        self.ranked = sorted(self.direct, key=lambda c: (-self.direct[c], c))
        self.parent = {}
        self.hierarchy = dict(self.direct)

    def getTotalSize(self):
        return self.total

    def getCollectionSize(self, collectionId):
        return self.direct.get(collectionId, 0)

    def getTopCollections(self, k):
        return self.ranked[:k]

    def setParent(self, childId, parentId):
        add = self.hierarchy.get(childId, 0)
        self.parent[childId] = parentId
        node = parentId
        while node is not None:
            self.hierarchy[node] = self.hierarchy.get(node, 0) + add
            node = self.parent.get(node)

    def getHierarchySize(self, collectionId):
        return self.hierarchy.get(collectionId, 0)


def solve(operation_names, argument_lists):
    if operation_names[0] != 'FileSystemStats' or len(argument_lists[0]) != 1:
        raise ValueError('exact initial constructor required')
    instance = FileSystemStats(*argument_lists[0])
    allowed = {'getTotalSize', 'getCollectionSize', 'getTopCollections', 'setParent', 'getHierarchySize'}
    voids = {'setParent'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
