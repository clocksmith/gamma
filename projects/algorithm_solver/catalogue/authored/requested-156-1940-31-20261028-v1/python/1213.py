"""Original frontend 1213 variant; qualification unknown."""


def solve(arr1, arr2, arr3):
    i = j = k = 0
    n1, n2, n3 = len(arr1), len(arr2), len(arr3)
    res = []
    while i < n1 and j < n2 and k < n3:
        a, b, c = arr1[i], arr2[j], arr3[k]
        if a == b == c:
            res.append(a)
            i += 1
            j += 1
            k += 1
        elif a <= b and a <= c:
            i += 1
        elif b <= a and b <= c:
            j += 1
        else:
            k += 1
    return res


arraysIntersection = solve


class Solution:
    def arraysIntersection(self, arr1, arr2, arr3):
        return solve(arr1, arr2, arr3)
