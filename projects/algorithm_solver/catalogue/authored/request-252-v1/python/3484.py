class Spreadsheet:
    def __init__(self, rows):
        self.rows = rows
        self.cells = {}

    def setCell(self, cell, value):
        self.cells[cell] = value

    def resetCell(self, cell):
        self.cells.pop(cell, None)

    def getValue(self, formula):
        total = 0
        for operand in formula[1:].split('+'):
            total += self.cells.get(operand, 0) if operand[0].isalpha() else int(operand)
        return total


def solve(operations, arguments):
    sheet = None
    result = []
    for operation, args in zip(operations, arguments):
        if operation == 'Spreadsheet':
            sheet = Spreadsheet(*args)
            result.append(None)
        else:
            result.append(getattr(sheet, operation)(*args))
    return result
