class Solution:
    def countSubMultisets(self, nums: list[int], l: int, r: int) -> int:
        frequencies = {}
        for value in nums:
            frequencies[value] = frequencies.get(value, 0) + 1
        modulus = 1000000007
        counts = [0] * (r + 1)
        counts[0] = frequencies.get(0, 0) + 1
        for value, multiplicity in frequencies.items():
            if value == 0 or value > r:
                continue
            following = [0] * (r + 1)
            excluded = (multiplicity + 1) * value
            for total in range(r + 1):
                ways = counts[total]
                if total >= value:
                    ways += following[total - value]
                if total >= excluded:
                    ways -= counts[total - excluded]
                following[total] = (ways + modulus) % modulus
            counts = following
        answer = 0
        for total in range(l, r + 1):
            answer = (answer + counts[total]) % modulus
        return answer
