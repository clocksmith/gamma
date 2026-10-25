class Solution:
    def clumsy(self, n):
        def product_group(first):
            if first >= 3:
                return first * (first - 1) // (first - 2)
            return first

        total = product_group(n)
        current = n - 3
        while current >= 1:
            total += current
            current -= 1
            if current >= 1:
                total -= product_group(current)
                current -= 3
        return total
