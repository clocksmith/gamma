# 336 — Palindrome Pairs. Original implementation; authored candidate, not independently qualified.
def solve(words):
    def boundaries(word):
        n = len(word)
        prefix, suffix = [False] * (n + 1), [False] * (n + 1)
        prefix[0] = suffix[n] = True
        # Manacher radii give all palindromic prefixes/suffixes in linear time.
        for even in (False, True):
            radius = [0] * n
            left, right = 0, -1
            for i in range(n):
                k = (0 if even else 1) if i > right else min(radius[left + right - i + int(even)], right - i + 1)
                while i - k - int(even) >= 0 and i + k < n and word[i - k - int(even)] == word[i + k]:
                    k += 1
                radius[i] = k
                start, end = i - k + int(not even), i + k - 1
                if start == 0:
                    prefix[end + 1] = True
                if end == n - 1:
                    suffix[start] = True
                if end > right:
                    left, right = start, end
        return prefix, suffix
    def node():
        return [{}, -1, []]
    root, flags = node(), []
    for index, word in enumerate(words):
        prefix, suffix = boundaries(word)
        flags.append(suffix)
        current = root
        for j in range(len(word) - 1, -1, -1):
            if prefix[j + 1]:
                current[2].append(index)
            if word[j] not in current[0]:
                current[0][word[j]] = node()
            current = current[0][word[j]]
        current[1] = index
        current[2].append(index)
    result = []
    for index, word in enumerate(words):
        current = root
        for j, char in enumerate(word):
            if current[1] >= 0 and current[1] != index and flags[index][j]:
                result.append([index, current[1]])
            current = current[0].get(char)
            if current is None:
                break
        else:
            result.extend([index, other] for other in current[2] if other != index)
    return result

palindromePairs = solve

class Solution:
    palindromePairs = staticmethod(solve)
