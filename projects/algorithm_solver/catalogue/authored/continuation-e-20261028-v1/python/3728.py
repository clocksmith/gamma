def solve(capacity):
    prefix = [0]
    for x in capacity:
        prefix.append(prefix[-1] + x)
    counts = {}
    answer = 0
    for r in range(2, len(capacity)):
        l = r - 2
        key = (capacity[l], prefix[l] + 2 * capacity[l])
        counts[key] = counts.get(key, 0) + 1
        answer += counts.get((capacity[r], prefix[r]), 0)
    return answer


class Solution:
    def countStableSubarrays(self, capacity):
        return solve(capacity)
