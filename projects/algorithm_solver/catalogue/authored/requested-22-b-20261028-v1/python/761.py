"""Original frontend 761 variant; qualification unknown."""

def solve(s):
    def largest(text):
        blocks = []
        balance = start = 0
        for i, ch in enumerate(text):
            balance += 1 if ch == '1' else -1
            if balance == 0:
                blocks.append('1' + largest(text[start + 1:i]) + '0')
                start = i + 1
        blocks.sort(reverse=True)
        return ''.join(blocks)
    return largest(s)


class Solution:
    def makeLargestSpecial(self, s):
        return solve(s)
