def solve(s):
    n = len(s)
    pal_two = bytearray([1]) * (n + 1)
    pal_one = bytearray([1]) * n
    almost_two = bytearray(n + 1)
    almost_one = bytearray([1]) * n
    answer = 1
    for length in range(2, n + 1):
        count = n - length + 1
        pal = bytearray(count)
        almost = bytearray(count)
        for l in range(count):
            same = s[l] == s[l + length - 1]
            pal[l] = same and bool(pal_two[l + 1])
            almost[l] = bool(pal_one[l] or pal_one[l + 1] or (same and almost_two[l + 1]))
            if almost[l]:
                answer = length
        pal_two, pal_one = pal_one, pal
        almost_two, almost_one = almost_one, almost
    return answer


class Solution:
    def almostPalindromic(self, s):
        return solve(s)
