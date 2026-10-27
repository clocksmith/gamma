"""168. Excel Sheet Column Title."""
def solve(columnNumber: int) -> str:
    result = []
    while columnNumber:
        columnNumber -= 1
        columnNumber, remainder = divmod(columnNumber, 26)
        result.append(chr(65 + remainder))
    return ''.join(reversed(result))

class Solution:
    def convertToTitle(self, columnNumber: int) -> str:
        return solve(columnNumber)
