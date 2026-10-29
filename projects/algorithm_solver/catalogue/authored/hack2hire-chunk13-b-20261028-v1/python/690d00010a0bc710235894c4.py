"""Hack2Hire 690d00010a0bc710235894c4 (Sparse Matrix Operation) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class SparseMatrix:
    def __init__(self, matrix):
        self.rows, self.cols = len(matrix), len(matrix[0])
        self.data = {}  # row -> {col: non-zero value}
        for i, row in enumerate(matrix):
            entries = {j: v for j, v in enumerate(row) if v != 0}
            if entries:
                self.data[i] = entries

    def get(self, row, col):
        entries = self.data.get(row)
        return entries.get(col, 0) if entries else 0

    def set(self, row, col, value):
        if value != 0:
            self.data.setdefault(row, {})[col] = value
        else:
            entries = self.data.get(row)
            if entries and col in entries:
                del entries[col]
                if not entries:
                    del self.data[row]

    def add(self, other):
        out = []
        for i in range(self.rows):
            acc = dict(self.data.get(i, {}))
            for j, v in enumerate(other[i]):
                if v != 0:
                    acc[j] = acc.get(j, 0) + v
            for j in sorted(acc):
                if acc[j] != 0:
                    out.append([i, j, acc[j]])
        return out

    def multiply(self, other):
        other_rows = [[(j, v) for j, v in enumerate(row) if v != 0] for row in other]
        out = []
        for i in sorted(self.data):
            acc = {}
            for t, a in self.data[i].items():
                for j, b in other_rows[t]:
                    acc[j] = acc.get(j, 0) + a * b
            for j in sorted(acc):
                if acc[j] != 0:
                    out.append([i, j, acc[j]])
        return out


def solve(operation_names, argument_lists):
    if operation_names[0] != 'SparseMatrix' or len(argument_lists[0]) != 1:
        raise ValueError('exact initial constructor required')
    instance = SparseMatrix(*argument_lists[0])
    allowed = {'get', 'set', 'add', 'multiply'}
    voids = {'set'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
