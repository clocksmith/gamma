class Solution:
    def countGoodTriplets(self, arr: list[int], a: int, b: int, c: int) -> int:
        count = 0
        for first in range(len(arr)):
            for second in range(first + 1, len(arr)):
                if abs(arr[first] - arr[second]) > a:
                    continue
                for third in range(second + 1, len(arr)):
                    if abs(arr[second] - arr[third]) <= b and abs(arr[first] - arr[third]) <= c:
                        count += 1
        return count
