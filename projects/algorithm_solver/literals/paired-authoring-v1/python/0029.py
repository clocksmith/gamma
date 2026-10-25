class Solution:
    def divide(self, dividend: int, divisor: int) -> int:
        negative = (dividend < 0) != (divisor < 0)
        # Negative magnitudes keep the minimum signed integer representable.
        remaining = -dividend if dividend > 0 else dividend
        chunk = -divisor if divisor > 0 else divisor
        multiple = -1
        chunks = []
        while chunk >= remaining:
            chunks.append((chunk, multiple))
            if chunk < -1073741824:
                break
            chunk += chunk
            multiple += multiple

        quotient = 0
        for chunk, multiple in reversed(chunks):
            if chunk >= remaining:
                remaining -= chunk
                quotient += multiple
        if quotient == 0:
            return 0
        if negative:
            return quotient
        if quotient == -2147483648:
            return 2147483647
        return -quotient
