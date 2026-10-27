"""395. Longest Substring with At Least K Repeating Characters. Enumerate the number of distinct lowercase letters; O(26*n) time."""

def solve(s: str, k: int) -> int:
    answer = 0
    for wanted in range(1, len(set(s)) + 1):
        counts = [0] * 26
        left = distinct = sufficient = 0
        for right, char in enumerate(s):
            index = ord(char) - 97
            if counts[index] == 0:
                distinct += 1
            counts[index] += 1
            if counts[index] == k:
                sufficient += 1
            while distinct > wanted:
                index = ord(s[left]) - 97
                if counts[index] == k:
                    sufficient -= 1
                counts[index] -= 1
                if counts[index] == 0:
                    distinct -= 1
                left += 1
            if distinct == sufficient:
                answer = max(answer, right - left + 1)
    return answer


class Solution:
    def longestSubstring(self, s: str, k: int) -> int:
        return solve(s, k)
