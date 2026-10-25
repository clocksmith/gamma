class Solution:
    def numRollsToTarget(self, n: int, k: int, target: int) -> int:
        modulus = 1000000007
        previous = [0] * (target + 1)
        previous[0] = 1
        for _ in range(n):
            current = [0] * (target + 1)
            for total in range(1, target + 1):
                ways = 0
                for face in range(1, min(k, total) + 1):
                    ways = (ways + previous[total - face]) % modulus
                current[total] = ways
            previous = current
        return previous[target]
