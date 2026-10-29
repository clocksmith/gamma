"""Hack2Hire 6a2194828b879849ebc11fd5 (Filter Unsafe Messages, variant 2). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown."""

_END = '$'


def solve(messages, unsafeWords):
    trie = {}
    for word in unsafeWords:
        node = trie
        for ch in word:
            node = node.setdefault(ch, {})
        node[_END] = True

    def unsafe(text):
        for start in range(len(text)):
            node, i = trie, start
            while i < len(text) and text[i] in node:
                node = node[text[i]]
                if _END in node:
                    return True
                i += 1
        return False

    return [[username, text] for username, text in messages if not unsafe(text)]


class Solution:
    def filterUnsafeMessages(self, messages, unsafeWords):
        return solve(messages, unsafeWords)
