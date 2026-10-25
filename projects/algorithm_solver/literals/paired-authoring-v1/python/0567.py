class Solution:
    def checkInclusion(self, s1: str, s2: str) -> bool:
        window_size = len(s1)
        if window_size == 0:
            return True
        if window_size > len(s2):
            return False

        counts = [0] * 26
        for value in s1:
            index = ord(value) - 97
            counts[index] += 1

        missing = window_size
        for right in range(len(s2)):
            incoming = ord(s2[right]) - 97
            if counts[incoming] > 0:
                missing -= 1
            counts[incoming] -= 1

            if right >= window_size:
                outgoing = ord(s2[right - window_size]) - 97
                counts[outgoing] += 1
                if counts[outgoing] > 0:
                    missing += 1

            if missing == 0:
                return True
        return False
