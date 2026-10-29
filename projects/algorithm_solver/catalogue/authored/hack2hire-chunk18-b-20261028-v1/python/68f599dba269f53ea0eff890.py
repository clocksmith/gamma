"""Hack2Hire 68f599dba269f53ea0eff890 (One-Hot Encoding of An Array) over an INFERRED spec; qualification unknown."""


def solve(arr):
    values = sorted(set(arr))
    index = {v: i for i, v in enumerate(values)}
    width = len(values)
    out = []
    for x in arr:
        row = [0] * width
        row[index[x]] = 1
        out.append(row)
    return out


class Solution:
    def oneHotEncode(self, arr):
        return solve(arr)
