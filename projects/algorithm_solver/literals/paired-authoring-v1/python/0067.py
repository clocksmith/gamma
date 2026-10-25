class Solution:
    def addBinary(self, a: str, b: str) -> str:
        left = len(a) - 1
        right = len(b) - 1
        carry = 0
        digits = []
        while left >= 0 or right >= 0 or carry > 0:
            total = carry
            if left >= 0:
                total += 1 if a[left] == "1" else 0
                left -= 1
            if right >= 0:
                total += 1 if b[right] == "1" else 0
                right -= 1
            digits.append("1" if total % 2 else "0")
            carry = total // 2
        digits.reverse()
        return "".join(digits)
