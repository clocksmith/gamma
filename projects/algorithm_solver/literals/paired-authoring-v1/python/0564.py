class Solution:
    def nearestPalindromic(self, n: str) -> str:
        length = len(n)
        value = int(n)
        prefix_length = (length + 1) // 2
        prefix = int(n[:prefix_length])
        candidates = [10 ** (length - 1) - 1, 10 ** length + 1]
        for change in (-1, 0, 1):
            leading = str(prefix + change)
            if len(leading) != prefix_length:
                continue
            reflected = leading if length % 2 == 0 else leading[:-1]
            candidates.append(int(leading + reflected[::-1]))

        best = None
        best_distance = 0
        for candidate in candidates:
            if candidate == value:
                continue
            distance = abs(candidate - value)
            if best is None or distance < best_distance or (distance == best_distance and candidate < best):
                best = candidate
                best_distance = distance
        return str(best)
