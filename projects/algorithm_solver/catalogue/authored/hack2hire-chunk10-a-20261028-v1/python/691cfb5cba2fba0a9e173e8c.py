"""Hack2Hire 691cfb5cba2fba0a9e173e8c (Design In-Memory SQL) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

import operator
import re

INTEGER = re.compile(r'0|-?[1-9][0-9]{0,8}')
OPS = {'=': operator.eq, '!=': operator.ne, '<': operator.lt, '<=': operator.le, '>': operator.gt, '>=': operator.ge}


class Table:
    def __init__(self, columns):
        self.columns = list(columns)
        self.index = {name: i for i, name in enumerate(columns)}
        self.types = None  # list of booleans (True = integer) fixed by the first stored row
        self.rows = []  # (original strings, typed values)


class SQLManager:
    def __init__(self):
        self.tables = {}

    def createTable(self, tableName, columnNames):
        self.tables[tableName] = Table(columnNames)

    def insert(self, tableName, values):
        table = self.tables.get(tableName)
        if table is None or len(values) != len(table.columns):
            return False
        kinds = [INTEGER.fullmatch(v) is not None for v in values]
        if table.types is not None and kinds != table.types:
            return False
        table.types = kinds
        table.rows.append((list(values), [int(v) if k else v for v, k in zip(values, kinds)]))
        return True

    def select(self, tableName, conditions, orderBy, ascending):
        table = self.tables.get(tableName)
        if table is None or not table.rows or (orderBy and orderBy not in table.index):
            return []
        tests = []
        for column, op, literal in conditions:
            i = table.index.get(column)
            if i is None:
                return []
            if table.types[i]:
                if INTEGER.fullmatch(literal) is None:
                    return []  # a non-integer literal matches no integer value
                literal = int(literal)
            tests.append((i, OPS[op], literal))
        hits = [row for row in table.rows if all(fn(row[1][i], lit) for i, fn, lit in tests)]
        if orderBy:
            j = table.index[orderBy]
            hits.sort(key=lambda row: row[1][j], reverse=not ascending)  # stable in both directions
        return [list(row[0]) for row in hits]


def solve(operation_names, argument_lists):
    if operation_names[0] != 'SQLManager' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = SQLManager(*argument_lists[0])
    allowed = {'createTable', 'insert', 'select'}
    voids = {'createTable'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
