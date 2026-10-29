"""Hack2Hire 6a1a0ed3c81f779dc6a2377c (Implement Dataset Join Operation, variant 2 of 4) over an INFERRED spec; qualification unknown."""


def solve(customerFile, processorFile, fieldName):
    ci = customerFile[0].split(',').index(fieldName)
    processor_header = processorFile[0].split(',')
    pi = processor_header.index(fieldName)
    index = {}  # key value -> processor rows in input order
    for row in processorFile[1:]:
        index.setdefault(row.split(',')[pi], []).append(row)
    padding = ',' * len(processor_header)
    out = [customerFile[0] + ',' + processorFile[0]]
    for row in customerFile[1:]:
        matches = index.get(row.split(',')[ci])
        if matches:
            for match in matches:
                out.append(row + ',' + match)
        else:
            out.append(row + padding)
    return out


class Solution:
    def joinDataSet(self, customerFile, processorFile, fieldName):
        return solve(customerFile, processorFile, fieldName)
