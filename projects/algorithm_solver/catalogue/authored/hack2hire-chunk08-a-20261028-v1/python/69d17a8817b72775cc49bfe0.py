"""Hack2Hire 69d17a8817b72775cc49bfe0 (Select Table and Set Color) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class Table:
    def __init__(self, numRows, numColumns):
        self.columns = numColumns
        self.stamp = 0
        self.table = (0, '')
        self.rows = {}
        self.cells = {}
        self.selection = None

    def selectTable(self):
        self.selection = ('table',)

    def selectRow(self, row):
        self.selection = ('row', row)

    def selectCell(self, row, col):
        self.selection = ('cell', row * self.columns + col)

    def setColor(self, color):
        if self.selection is None:
            return
        self.stamp += 1
        kind = self.selection[0]
        if kind == 'table':
            self.table = (self.stamp, color)
        elif kind == 'row':
            self.rows[self.selection[1]] = (self.stamp, color)
        else:
            self.cells[self.selection[1]] = (self.stamp, color)

    def getColor(self, row, col):
        best = self.table
        painted = self.rows.get(row)
        if painted is not None and painted[0] > best[0]:
            best = painted
        painted = self.cells.get(row * self.columns + col)
        if painted is not None and painted[0] > best[0]:
            best = painted
        return best[1]


def solve(operation_names, argument_lists):
    if operation_names[0] != 'Table' or len(argument_lists[0]) != 2:
        raise ValueError('exact initial constructor required')
    instance = Table(*argument_lists[0])
    allowed = {'selectTable', 'selectRow', 'selectCell', 'setColor', 'getColor'}
    voids = {'selectTable', 'selectRow', 'selectCell', 'setColor'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
