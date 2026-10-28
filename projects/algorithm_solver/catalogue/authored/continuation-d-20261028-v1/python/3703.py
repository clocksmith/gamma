"""Original development candidate for frontend 3703; qualification pending."""

def solve(s, k):
    pattern = '(' * k + ')' * k
    prefix = [0] * len(pattern)
    matched = 0
    for i in range(1, len(pattern)):
        while matched and pattern[i] != pattern[matched]:
            matched = prefix[matched - 1]
        if pattern[i] == pattern[matched]:
            matched += 1
        prefix[i] = matched
    stack, states = [], []
    matched = 0
    for char in s:
        while matched and char != pattern[matched]:
            matched = prefix[matched - 1]
        if char == pattern[matched]:
            matched += 1
        stack.append(char)
        states.append(matched)
        if matched == len(pattern):
            del stack[-len(pattern):]
            del states[-len(pattern):]
            matched = states[-1] if states else 0
    return ''.join(stack)


class Solution:
    def removeSubstring(self, s, k):
        return solve(s, k)
