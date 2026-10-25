class Solution:
    def getMaxFunctionValue(self, receiver: list[int], k: int) -> int:
        jumps = [receiver.copy()]
        sums = [receiver.copy()]
        block = 2
        while block <= k:
            previous_jumps = jumps[-1]
            previous_sums = sums[-1]
            following_jumps = []
            following_sums = []
            for node in range(len(receiver)):
                middle = previous_jumps[node]
                following_jumps.append(previous_jumps[middle])
                following_sums.append(previous_sums[node] + previous_sums[middle])
            jumps.append(following_jumps)
            sums.append(following_sums)
            block *= 2
        best = 0
        for start in range(len(receiver)):
            node = start
            total = start
            remaining = k
            level = 0
            while remaining > 0:
                if remaining % 2 == 1:
                    total += sums[level][node]
                    node = jumps[level][node]
                remaining //= 2
                level += 1
            best = max(best, total)
        return best
