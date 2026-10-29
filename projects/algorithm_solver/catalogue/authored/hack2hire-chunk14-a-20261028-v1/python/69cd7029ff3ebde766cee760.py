"""Hack2Hire 69cd7029ff3ebde766cee760 (Stream to Matrix Row Transformer) over an INFERRED spec; qualification unknown."""


def solve(codes, records):
    columns = sorted(codes)
    index = {code: i for i, code in enumerate(columns)}
    groups = {}
    for timestamp, code, value in records:
        if code in index:
            groups.setdefault(timestamp, []).append((index[code], value))
    current = [None] * len(columns)
    rows = []
    for timestamp in sorted(groups):
        for column, value in groups[timestamp]:
            current[column] = value
        rows.append([timestamp] + current)
    return rows


class Solution:
    def buildRows(self, codes, records):
        return solve(codes, records)
