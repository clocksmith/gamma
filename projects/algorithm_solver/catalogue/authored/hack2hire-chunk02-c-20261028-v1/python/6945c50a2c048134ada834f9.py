"""Hack2Hire 6945c50a2c048134ada834f9 (Chat Message Range Merge, variant 1) over an INFERRED spec; qualification unknown."""

def solve(messages, queries):
    position = {message[0]: index for index, message in enumerate(messages)}
    last = len(messages) - 1
    intervals = sorted((max(0, position[target] - before), min(last, position[target] + after)) for target, before, after in queries)
    merged = []
    for start, end in intervals:
        if merged and start <= merged[-1][1] + 1:
            if end > merged[-1][1]:
                merged[-1][1] = end
        else:
            merged.append([start, end])
    return [[messages[start][0], messages[end][0]] for start, end in merged]


class Solution:
    def mergeChatRanges(self, messages, queries):
        return solve(messages, queries)
