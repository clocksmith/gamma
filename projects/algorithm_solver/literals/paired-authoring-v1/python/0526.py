class Solution:
    def countArrangement(self, n: int) -> int:
        used = [False] * (n + 1)

        def count_from(position: int) -> int:
            if position > n:
                return 1
            total = 0
            for value in range(1, n + 1):
                if used[value] or (value % position != 0 and position % value != 0):
                    continue
                used[value] = True
                total += count_from(position + 1)
                used[value] = False
            return total

        return count_from(1)
