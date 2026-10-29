"""Hack2Hire 68d8465eae12841706c1fc6e (Design File Search Tool) over an INFERRED spec; qualification unknown."""


def is_word_char(c):
    return 'a' <= c <= 'z' or 'A' <= c <= 'Z' or '0' <= c <= '9'


def lower_ascii(s):
    return ''.join(chr(ord(c) + 32) if 'A' <= c <= 'Z' else c for c in s)


def count_in_line(line, target):
    count = 0
    i, n = 0, len(line)
    while i < n:
        if is_word_char(line[i]):
            j = i
            while j < n and is_word_char(line[j]):
                j += 1
            if j - i == len(target) and lower_ascii(line[i:j]) == target:
                count += 1
            i = j
        else:
            i += 1
    return count


def solve(files, word):
    target = lower_ascii(word)
    result = []
    for name, lines in files:
        total = 0
        hits = []
        for line in lines:
            c = count_in_line(line, target)
            if c:
                total += c
                hits.append(line)
        if total:
            result.append([name, str(total)] + hits)
    return result


class Solution:
    def searchFiles(self, files, word):
        return solve(files, word)
