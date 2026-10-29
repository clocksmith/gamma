"""Hack2Hire 6a1a0f0dc81f779dc6a2377e (Implement Dataset Join Operation, variant 4 of 4) over an INFERRED spec; qualification unknown."""


def solve(customerFile, processorFile, fieldNames):
    customer_header = customerFile[0].split(',')
    processor_header = processorFile[0].split(',')
    ci = [customer_header.index(f) for f in fieldNames]
    pi = [processor_header.index(f) for f in fieldNames]
    index = {}  # composite key (values joined by a comma, which values never contain) -> processor rows
    for row in processorFile[1:]:
        values = row.split(',')
        index.setdefault(','.join(values[i] for i in pi), []).append(row)
    out = [customerFile[0] + ',' + processorFile[0]]
    for row in customerFile[1:]:
        values = row.split(',')
        for match in index.get(','.join(values[i] for i in ci), ()):
            out.append(row + ',' + match)
    return out


class Solution:
    def joinDataSet(self, customerFile, processorFile, fieldNames):
        return solve(customerFile, processorFile, fieldNames)
