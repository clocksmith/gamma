class Solution:
    def convert(self, s: str, numRows: int) -> str:
        if numRows == 1 or numRows >= len(s):
            return s

        rows = [[] for _ in range(numRows)]
        row = 0
        direction = 1
        for character in s:
            rows[row].append(character)
            if row == 0:
                direction = 1
            elif row == numRows - 1:
                direction = -1
            row += direction
        ordered = []
        for characters in rows:
            ordered.append("".join(characters))
        return "".join(ordered)
