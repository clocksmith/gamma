"""Hack2Hire 677c6cdc5cbaff553b53b06c (Tail N Lines) over an INFERRED spec; qualification unknown."""


def solve(text, n):
    if n == 0 or not text:
        return ''
    ring = [0] * n
    count = 0
    start = 0
    length = len(text)
    while start < length:
        ring[count % n] = start
        count += 1
        newline = text.find('\n', start)
        if newline < 0:
            break
        start = newline + 1
    oldest = ring[count % n] if count > n else ring[0]
    return text[oldest:]


class Solution:
    def tail(self, text, n):
        return solve(text, n)
