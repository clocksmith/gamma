"""Hack2Hire 6a1a0ee5c81f779dc6a2377d (Implement Dataset Join Operation, variant 3 of 4) over an INFERRED spec; qualification unknown."""


def solve(customerFile, processorFile, fieldName):
    customer_header = customerFile[0].split(',')
    processor_header = processorFile[0].split(',')
    ci = customer_header.index(fieldName)
    pi = processor_header.index(fieldName)
    index = {}  # key value -> processor row numbers in input order
    for r, row in enumerate(processorFile[1:]):
        index.setdefault(row.split(',')[pi], []).append(r)
    used = [False] * (len(processorFile) - 1)
    padding = ',' * len(processor_header)
    out = [customerFile[0] + ',' + processorFile[0]]
    for row in customerFile[1:]:
        matches = index.get(row.split(',')[ci])
        if matches:
            for r in matches:
                used[r] = True
                out.append(row + ',' + processorFile[r + 1])
        else:
            out.append(row + padding)
    lead = ',' * len(customer_header)
    for r, flag in enumerate(used):
        if not flag:
            out.append(lead + processorFile[r + 1])
    return out


class Solution:
    def joinDataSet(self, customerFile, processorFile, fieldName):
        return solve(customerFile, processorFile, fieldName)
