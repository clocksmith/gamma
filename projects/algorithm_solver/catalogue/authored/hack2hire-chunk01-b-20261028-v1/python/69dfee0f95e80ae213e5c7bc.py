"""Hack2Hire 69dfee0f95e80ae213e5c7bc (Find Text Before Stop Words, variant 2: streamed chunks). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown."""


def solve(chunks, stopWords):
    prefixes, longest = set(), 0
    for word in stopWords:
        longest = max(longest, len(word))
        for i in range(1, len(word)):
            prefixes.add(word[:i])

    def earliest(text):
        found = -1
        for word in stopWords:
            position = text.find(word)
            if position >= 0 and (found < 0 or position < found):
                found = position
        return found

    out, pending, stopped = [], '', False
    for chunk in chunks:
        if stopped:
            out.append('')
            continue
        pending += chunk
        hold = len(pending)
        for start in range(max(0, len(pending) - longest + 1), len(pending)):
            if pending[start:] in prefixes:
                hold = start
                break
        position = earliest(pending)
        if 0 <= position <= hold:
            out.append(pending[:position])
            pending, stopped = '', True
        else:
            out.append(pending[:hold])
            pending = pending[hold:]
    if stopped:
        out.append('')
    else:
        position = earliest(pending)
        out.append(pending if position < 0 else pending[:position])
    return out


class Solution:
    def streamBeforeStopWords(self, chunks, stopWords):
        return solve(chunks, stopWords)
