class Solution:
    def maxSumTwoNoOverlap(self, nums, firstLen, secondLen):
        prefix = [0]
        for value in nums:
            prefix.append(prefix[-1] + value)

        def first_before_second(first_length, second_length):
            best_first = prefix[first_length]
            best_total = prefix[first_length + second_length]
            for end in range(first_length + second_length, len(nums) + 1):
                split = end - second_length
                best_first = max(best_first, prefix[split] - prefix[split - first_length])
                best_total = max(best_total, best_first + prefix[end] - prefix[split])
            return best_total

        return max(first_before_second(firstLen, secondLen),
                   first_before_second(secondLen, firstLen))
