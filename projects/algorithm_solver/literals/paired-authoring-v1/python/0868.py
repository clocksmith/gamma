class Solution:
    def binaryGap(self, n: int) -> int:
        position = 0
        previous = -1
        longest = 0
        while n > 0:
            if n % 2 == 1:
                if previous >= 0:
                    longest = max(longest, position - previous)
                previous = position
            n //= 2
            position += 1
        return longest
