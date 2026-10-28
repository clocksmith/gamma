def solve(s, target):
    counts = [s.count(chr(97 + i)) for i in range(26)]
    odds = [i for i, count in enumerate(counts) if count % 2]
    if len(odds) > 1:
        return ''
    middle = chr(97 + odds[0]) if odds else ''
    counts = [x // 2 for x in counts]
    half = len(s) // 2
    prefix = []
    while len(prefix) < half:
        c = ord(target[len(prefix)]) - 97
        if not counts[c]:
            break
        counts[c] -= 1
        prefix.append(c)
    def palindrome(left):
        text = ''.join(chr(97 + c) for c in left)
        return text + middle + text[::-1]
    if len(prefix) == half:
        result = palindrome(prefix)
        if result > target:
            return result
    pos = len(prefix)
    while True:
        if pos < half:
            for c in range(ord(target[pos]) - 96, 26):
                if counts[c]:
                    counts[c] -= 1
                    tail = [j for j in range(26) for _ in range(counts[j])]
                    return palindrome(prefix + [c] + tail)
        if pos == 0:
            return ''
        pos -= 1
        counts[prefix.pop()] += 1


class Solution:
    def lexPalindromicPermutation(self, s, target):
        return solve(s, target)
