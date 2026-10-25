class Solution:
    def largestTimeFromDigits(self, arr):
        best = -1
        for first in range(4):
            for second in range(4):
                if second == first:
                    continue
                for third in range(4):
                    if third == first or third == second:
                        continue
                    fourth = 6 - first - second - third
                    hours = arr[first] * 10 + arr[second]
                    minutes = arr[third] * 10 + arr[fourth]
                    if hours < 24 and minutes < 60:
                        best = max(best, hours * 60 + minutes)
        if best < 0:
            return ""
        return str(best // 60).rjust(2, "0") + ":" + str(best % 60).rjust(2, "0")
