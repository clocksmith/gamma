class Solution:
    def numberOfWays(self, startPos: int, endPos: int, k: int) -> int:
        distance = abs(endPos - startPos)
        if distance > k or (k - distance) % 2 != 0:
            return 0
        chosen = (k - distance) // 2
        counts = [0] * (chosen + 1)
        counts[0] = 1
        modulus = 1000000007
        for steps in range(1, k + 1):
            for index in range(min(steps, chosen), 0, -1):
                counts[index] = (counts[index] + counts[index - 1]) % modulus
        return counts[chosen]
