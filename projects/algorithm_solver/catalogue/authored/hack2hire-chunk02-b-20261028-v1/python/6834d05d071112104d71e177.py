"""Original Hack2Hire 6834d05d071112104d71e177 variant over an INFERRED specification; qualification unknown."""


def solve(encoded):
    n, results, parts = len(encoded), [], []

    def walk(i, previous):
        if i == n:
            results.append(''.join(parts))
            return
        for size in (1, 2):
            if i + size < n and encoded[i] != '0':
                digit = encoded[i + size]
                if digit != previous:
                    parts.append(digit * int(encoded[i:i + size]))
                    walk(i + size + 1, digit)
                    parts.pop()
    walk(0, '')
    return sorted(results)


class Solution:
    def reverseCountAndSay(self, encoded):
        return solve(encoded)
