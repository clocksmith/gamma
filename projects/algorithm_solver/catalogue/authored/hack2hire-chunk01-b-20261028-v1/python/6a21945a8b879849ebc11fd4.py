"""Hack2Hire 6a21945a8b879849ebc11fd4 (Filter Unsafe Messages, variant 1). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown."""


def solve(messages, unsafeWords):
    unsafe = set(unsafeWords)
    out = []
    for username, text in messages:
        if not any(token in unsafe for token in text.split(' ') if token):
            out.append([username, text])
    return out


class Solution:
    def filterUnsafeMessages(self, messages, unsafeWords):
        return solve(messages, unsafeWords)
