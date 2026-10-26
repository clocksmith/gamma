"""1520. Maximum Number of Non-Overlapping Substrings.

Expand minimal closed character intervals, then select earliest finishes; O(26*n) time and O(26) auxiliary space, excluding output.
"""

def solve(s: str) -> list[str]:
    first, last = {}, {}
    for index, char in enumerate(s):
        first.setdefault(char, index)
        last[char] = index
    intervals = []
    for char, start in first.items():
        end = last[char]
        index = start
        while index <= end and first[s[index]] >= start:
            end = max(end, last[s[index]])
            index += 1
        if index > end:
            intervals.append((end, start))
    intervals.sort(key=lambda item: (item[0], -item[1]))
    answer = []
    previous = -1
    for end, start in intervals:
        if start > previous:
            answer.append(s[start:end + 1])
            previous = end
    return answer


class Solution:
    def maxNumOfSubstrings(self, s: str) -> list[str]:
        return solve(s)
