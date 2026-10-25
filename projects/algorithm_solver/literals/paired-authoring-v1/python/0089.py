class Solution:
    def grayCode(self, n: int) -> list[int]:
        codes = [0]
        bit = 1
        for _ in range(n):
            for index in range(len(codes) - 1, -1, -1):
                codes.append(bit + codes[index])
            bit *= 2
        return codes
