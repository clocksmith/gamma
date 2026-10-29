"""Hack2Hire 6a1a0cc4c81f779dc6a2376b (Implement Dataset Join Operation, variant 1 of 4) over an INFERRED spec; qualification unknown."""


def solve(customerFile, processorFile, fieldName):
    ci = customerFile[0].split(',').index(fieldName)
    pi = processorFile[0].split(',').index(fieldName)
    index = {}  # key value -> processor rows in input order
    for row in processorFile[1:]:
        index.setdefault(row.split(',')[pi], []).append(row)
    out = [customerFile[0] + ',' + processorFile[0]]
    for row in customerFile[1:]:
        for match in index.get(row.split(',')[ci], ()):
            out.append(row + ',' + match)
    return out


class Solution:
    def joinDataSet(self, customerFile, processorFile, fieldName):
        return solve(customerFile, processorFile, fieldName)
