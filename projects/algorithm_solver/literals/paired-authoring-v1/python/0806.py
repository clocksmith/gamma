class Solution:
    def numberOfLines(self, widths: list[int], s: str) -> list[int]:
        lines = 1
        used = 0
        for character in s:
            width = widths[ord(character) - 97]
            if used + width > 100:
                lines += 1
                used = 0
            used += width
        return [lines, used]
