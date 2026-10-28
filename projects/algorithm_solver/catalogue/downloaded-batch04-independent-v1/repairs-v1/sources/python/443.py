"""443. String Compression (Medium).

Specification: https://leetcode.com/problems/string-compression/description/
"""


def _count_digits(count):
    divisor = 1
    while divisor * 10 <= count:
        divisor *= 10
    while divisor:
        yield chr(48 + count // divisor)
        count %= divisor
        divisor //= 10


def _compress_in_place(chars):
    read = write = 0
    while read < len(chars):
        first = read
        value = chars[read]
        while read < len(chars) and chars[read] == value:
            read += 1
        chars[write] = value
        write += 1
        if read - first > 1:
            for digit in _count_digits(read - first):
                chars[write] = digit
                write += 1
    return write


def solve(chars: list[str]) -> list[str]:
    result = []
    read = 0
    while read < len(chars):
        first = read
        value = chars[read]
        while read < len(chars) and chars[read] == value:
            read += 1
        result.append(value)
        if read - first > 1:
            for digit in _count_digits(read - first):
                result.append(digit)
    return result


class Solution:
    def compress(self, chars: list[str]) -> int:
        return _compress_in_place(chars)
