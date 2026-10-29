"""Hack2Hire 695ecf112e3ae59d53a81ea7 (Multithreaded Array Sort) over an INFERRED spec; qualification unknown."""

def _merge(x, y):
    out, i, j = [], 0, 0
    while i < len(x) and j < len(y):
        if y[j] < x[i]:
            out.append(y[j])
            j += 1
        else:
            out.append(x[i])
            i += 1
    out.extend(x[i:])
    out.extend(y[j:])
    return out


def solve(nums, k):
    size, extra = divmod(len(nums), k)
    runs, start = [], 0
    for t in range(k):
        length = size + (1 if t < extra else 0)
        if length:
            runs.append(sorted(nums[start:start + length]))  # one "thread": reads and sorts only its own segment
        start += length
    while len(runs) > 1:
        runs = [_merge(runs[i], runs[i + 1]) if i + 1 < len(runs) else runs[i] for i in range(0, len(runs), 2)]
    return runs[0] if runs else []


class Solution:
    def sortWithThreads(self, nums, k):
        return solve(nums, k)
