def prefix_lengths(pattern: str) -> list[int]:
    prefix = [0] * len(pattern)
    matched = 0
    for index in range(1, len(pattern)):
        while matched > 0 and pattern[index] != pattern[matched]:
            matched = prefix[matched - 1]
        if pattern[index] == pattern[matched]:
            matched += 1
        prefix[index] = matched
    return prefix


class Solution:
    def repeatedStringMatch(self, a: str, b: str) -> int:
        if not b:
            return 0

        prefix = prefix_lengths(b)
        matched = 0
        for index in range(len(a) + len(b) - 1):
            character = a[index % len(a)]
            while matched > 0 and character != b[matched]:
                matched = prefix[matched - 1]
            if character == b[matched]:
                matched += 1
            if matched == len(b):
                return index // len(a) + 1
        return -1
