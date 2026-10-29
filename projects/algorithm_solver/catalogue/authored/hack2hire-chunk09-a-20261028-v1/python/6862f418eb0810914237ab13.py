"""Hack2Hire 6862f418eb0810914237ab13 (API Path Matching) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class APIMatchingSystem:
    def __init__(self):
        self.root = [None, {}]  # [handler or None, children by segment]

    def registerPath(self, path, handler):
        node = self.root
        if path != '/':
            for seg in path[1:].split('/'):
                child = node[1].get(seg)
                if child is None:
                    child = [None, {}]
                    node[1][seg] = child
                node = child
        node[0] = handler

    def matchPath(self, path):
        node = self.root
        best = node[0]
        if path != '/':
            for seg in path[1:].split('/'):
                node = node[1].get(seg)
                if node is None:
                    break
                if node[0] is not None:
                    best = node[0]
        return '' if best is None else best


def solve(operation_names, argument_lists):
    if operation_names[0] != 'APIMatchingSystem' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = APIMatchingSystem(*argument_lists[0])
    allowed = {'registerPath', 'matchPath'}
    voids = {'registerPath'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
