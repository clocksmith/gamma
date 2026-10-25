class Solution:
    def digitsCount(self, digit, low, high):
        def count_through(bound):
            total = 0
            factor = 1
            while factor <= bound:
                higher = bound // (factor * 10)
                current = (bound // factor) % 10
                lower = bound % factor
                if digit != 0:
                    total += higher * factor
                    if current > digit:
                        total += factor
                    elif current == digit:
                        total += lower + 1
                elif higher > 0:
                    total += (higher - 1) * factor
                    total += lower + 1 if current == 0 else factor
                factor *= 10
            return total
        return count_through(high) - count_through(low - 1)
