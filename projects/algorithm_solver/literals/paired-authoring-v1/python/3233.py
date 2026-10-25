class Solution:
    def nonSpecialCount(self, l: int, r: int) -> int:
        left = 0
        right = 31623
        while left < right:
            middle = left + (right - left + 1) // 2
            if middle * middle <= r:
                left = middle
            else:
                right = middle - 1
        limit = left
        prime = [True] * (limit + 1)
        prime[0] = False
        if limit >= 1:
            prime[1] = False
        candidate = 2
        while candidate * candidate <= limit:
            if prime[candidate]:
                for multiple in range(candidate * candidate, limit + 1, candidate):
                    prime[multiple] = False
            candidate += 1
        special = 0
        for value in range(2, limit + 1):
            if prime[value] and value * value >= l:
                special += 1
        return r - l + 1 - special
