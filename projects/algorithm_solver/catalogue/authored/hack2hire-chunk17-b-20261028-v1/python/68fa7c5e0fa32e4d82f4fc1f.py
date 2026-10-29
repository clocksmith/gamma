"""Hack2Hire 68fa7c5e0fa32e4d82f4fc1f (URL Router Design) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


def _segments(path):
    return [] if path == '/' else path[1:].split('/')


class Router:
    def __init__(self):
        # trie node: [children by segment, handler or None]
        self.root = [{}, None]

    def addRoute(self, pattern, handler):
        node = self.root
        for segment in _segments(pattern):
            child = node[0].get(segment)
            if child is None:
                child = [{}, None]
                node[0][segment] = child
            node = child
        node[1] = handler

    def callRoute(self, path):
        segments = _segments(path)
        size = len(segments)
        best_count = size + 1
        best = ''
        # depth-first, literal child before '*', so the first match at a given wildcard count is the left-to-right most specific
        stack = [(self.root, 0, 0)]
        while stack:
            node, depth, wild = stack.pop()
            if wild >= best_count:
                continue
            if depth == size:
                if node[1] is not None:
                    best_count = wild
                    best = node[1]
                continue
            children = node[0]
            star = children.get('*')
            if star is not None:
                stack.append((star, depth + 1, wild + 1))
            literal = children.get(segments[depth])
            if literal is not None and segments[depth] != '*':
                stack.append((literal, depth + 1, wild))
        return best


def solve(operation_names, argument_lists):
    if operation_names[0] != 'Router' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = Router(*argument_lists[0])
    allowed = {'addRoute', 'callRoute'}
    voids = {'addRoute'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
