"""Hack2Hire 677595ec0d31dc201f712037 (Connect Points in 2D Matrix) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class PointMatrix:
    def __init__(self):
        self.points = set()
        self.row_points = {}
        self.col_points = {}
        self.parent = {}

    def _find(self, key):
        parent = self.parent
        root = key
        while parent[root] != root:
            root = parent[root]
        while parent[key] != root:
            parent[key], key = root, parent[key]
        return root

    def addPoint(self, row, col):
        if (row, col) in self.points:
            return None
        self.points.add((row, col))
        self.row_points.setdefault(row, []).append(col)
        self.col_points.setdefault(col, []).append(row)
        r, c = ('r', row), ('c', col)
        self.parent.setdefault(r, r)
        self.parent.setdefault(c, c)
        a, b = self._find(r), self._find(c)
        if a != b:
            self.parent[a] = b
        return None

    def isConnected(self, point1, point2):
        p, q = (point1[0], point1[1]), (point2[0], point2[1])
        if p not in self.points or q not in self.points:
            return False
        return self._find(('r', p[0])) == self._find(('r', q[0]))

    def getMinSteps(self, start, end):
        s, e = (start[0], start[1]), (end[0], end[1])
        if s not in self.points or e not in self.points:
            return -1
        if s == e:
            return 0
        if self._find(('r', s[0])) != self._find(('r', e[0])):
            return -1
        seen_rows, seen_cols = {s[0]}, {s[1]}
        frontier = [(True, s[0]), (False, s[1])]
        steps = 0
        while frontier:
            nxt = []
            for is_row, line in frontier:
                if is_row:
                    for col in self.row_points[line]:
                        if (line, col) == e:
                            return steps + 1
                        if col not in seen_cols:
                            seen_cols.add(col)
                            nxt.append((False, col))
                else:
                    for row in self.col_points[line]:
                        if (row, line) == e:
                            return steps + 1
                        if row not in seen_rows:
                            seen_rows.add(row)
                            nxt.append((True, row))
            frontier = nxt
            steps += 1
        return -1


def solve(operation_names, argument_lists):
    if operation_names[0] != 'PointMatrix' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = PointMatrix(*argument_lists[0])
    allowed = {'addPoint', 'isConnected', 'getMinSteps'}
    voids = {'addPoint'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
