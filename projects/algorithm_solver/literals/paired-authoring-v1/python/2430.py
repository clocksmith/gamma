def z_values(text: str) -> list[int]:
    values = [0] * len(text)
    left = 0
    right = 0
    for index in range(1, len(text)):
        if index < right:
            values[index] = min(right - index, values[index - left])
        while index + values[index] < len(text) and text[values[index]] == text[index + values[index]]:
            values[index] += 1
        if index + values[index] > right:
            left = index
            right = index + values[index]
    return values


class Solution:
    def deleteString(self, s: str) -> int:
        best = [0] * (len(s) + 1)
        for start in range(len(s) - 1, -1, -1):
            suffix = s[start:]
            matches = z_values(suffix)
            best[start] = 1
            for length in range(1, len(suffix) // 2 + 1):
                if matches[length] >= length:
                    best[start] = max(best[start], 1 + best[start + length])
        return best[0]
