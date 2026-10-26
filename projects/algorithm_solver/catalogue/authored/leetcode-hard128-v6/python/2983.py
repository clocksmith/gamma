"""2983. Palindrome Rearrangement Queries.

Mirror both halves, subtract fixed-position demands, and compare remaining counts; O(26*(n+q)) time and space. Inputs are preserved.
"""

def solve(s: str, queries: list[list[int]]) -> list[bool]:
    half = len(s) // 2
    left, right = s[:half], s[half:][::-1]
    prefix_left = [[0] * 26]
    prefix_right = [[0] * 26]
    mismatch = [0]
    for a, b in zip(left, right):
        first, second = prefix_left[-1][:], prefix_right[-1][:]
        first[ord(a) - 97] += 1
        second[ord(b) - 97] += 1
        prefix_left.append(first)
        prefix_right.append(second)
        mismatch.append(mismatch[-1] + (a != b))

    def mismatches(a, b):
        return 0 if a > b else mismatch[b + 1] - mismatch[a]

    answer = []
    for a, b, c, d in queries:
        c, d = len(s) - 1 - d, len(s) - 1 - c
        start, end = max(a, c), min(b, d)
        if mismatch[-1] - mismatches(a, b) - mismatches(c, d) + mismatches(start, end):
            answer.append(False)
            continue
        valid = True
        for letter in range(26):
            overlap_left = prefix_left[end + 1][letter] - prefix_left[start][letter] if start <= end else 0
            overlap_right = prefix_right[end + 1][letter] - prefix_right[start][letter] if start <= end else 0
            available_left = prefix_left[b + 1][letter] - prefix_left[a][letter] - prefix_right[b + 1][letter] + prefix_right[a][letter] + overlap_right
            available_right = prefix_right[d + 1][letter] - prefix_right[c][letter] - prefix_left[d + 1][letter] + prefix_left[c][letter] + overlap_left
            if available_left < 0 or available_right < 0 or available_left != available_right:
                valid = False
                break
        answer.append(valid)
    return answer


class Solution:
    def canMakePalindromeQueries(self, s: str, queries: list[list[int]]) -> list[bool]:
        return solve(s, queries)
