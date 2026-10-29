"""Original frontend 321 variant; qualification unknown."""


def _max_subseq(arr, t):
    if t == 0:
        return []
    drop = len(arr) - t
    stack = []
    for d in arr:
        while drop > 0 and stack and stack[-1] < d:
            stack.pop()
            drop -= 1
        stack.append(d)
    return stack[:t]


def _greater_suffix(a, i, b, j):
    m, n = len(a), len(b)
    while i < m and j < n and a[i] == b[j]:
        i += 1
        j += 1
    if j == n:
        return True
    if i == m:
        return False
    return a[i] > b[j]


def solve(nums1, nums2, k):
    m, n = len(nums1), len(nums2)
    start = max(0, k - n)
    end = min(k, m)
    best = None
    for s1 in range(start, end + 1):
        a = _max_subseq(nums1, s1)
        b = _max_subseq(nums2, k - s1)
        merged = [0] * k
        i = j = 0
        for idx in range(k):
            if _greater_suffix(a, i, b, j):
                merged[idx] = a[i]
                i += 1
            else:
                merged[idx] = b[j]
                j += 1
        if best is None or merged > best:
            best = merged
    return best


maxNumber = solve


class Solution:
    def maxNumber(self, nums1, nums2, k):
        return solve(nums1, nums2, k)
