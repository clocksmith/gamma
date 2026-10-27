"""443. String Compression. Required in-place prefix rewrite; returns its length and leaves the suffix unspecified."""

def solve(chars: list[str]) -> int:
    read = write = 0
    while read < len(chars):
        end = read + 1
        while end < len(chars) and chars[end] == chars[read]:
            end += 1
        chars[write] = chars[read]
        write += 1
        if end - read > 1:
            for digit in str(end - read):
                chars[write] = digit
                write += 1
        read = end
    return write


class Solution:
    def compress(self, chars: list[str]) -> int:
        return solve(chars)
