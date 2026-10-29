"""Hack2Hire 69f78c6830f41dfd539fc6dc (Design a Spreadsheet with Formula Evaluation, level 1) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


def _parse(value):
    if value[0] != '=':
        return [int(value)]
    return [term if term[0].isalpha() else int(term) for term in value[1:].split('+')]


class Spreadsheet:
    def __init__(self):
        self.cells = {}

    def resetCell(self, cell):
        self.cells.pop(cell, None)

    def getCell(self, cell):
        cells = self.cells
        memo = {}
        stack = [cell]
        while stack:
            name = stack[-1]
            if name in memo:
                stack.pop()
                continue
            terms = cells.get(name, ())
            pending = [t for t in terms if type(t) is str and t not in memo]
            if pending:
                stack.extend(pending)
                continue
            stack.pop()
            memo[name] = sum(memo[t] if type(t) is str else t for t in terms)
        return memo[cell]

    def setCell(self, cell, value):
        self.cells[cell] = _parse(value)


def solve(operation_names, argument_lists):
    if operation_names[0] != 'Spreadsheet' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = Spreadsheet(*argument_lists[0])
    allowed = ['setCell', 'getCell', 'resetCell']
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        result.append(getattr(instance, name)(*arguments))
    return result
