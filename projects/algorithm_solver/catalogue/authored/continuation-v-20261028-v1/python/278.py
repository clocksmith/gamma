class Solution:
    def firstBadVersion(self, n):
        # Official external API must be supplied by the reviewed runtime.
        # No fallback, stub, namespace scan, or hidden-answer argument.
        api = globals()['isBadVersion']
        low, high = 1, n
        while low < high:
            middle = low + (high - low) // 2
            if api(middle):
                high = middle
            else:
                low = middle + 1
        return low
