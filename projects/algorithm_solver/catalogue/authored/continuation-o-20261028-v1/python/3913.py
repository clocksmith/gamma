"""Original frontend 3913 variant; qualification unknown."""

def solve(s):
    counts, first = {}, {}
    for i, char in enumerate(s):
        if char in 'aeiou':
            counts[char] = counts.get(char, 0) + 1
            first.setdefault(char, i)
    vowels = ''.join(char * counts[char] for char in sorted(counts, key=lambda c: (-counts[c], first[c])))
    iterator = iter(vowels)
    return ''.join(next(iterator) if char in 'aeiou' else char for char in s)


class Solution:
    def sortVowels(self, s):
        return solve(s)
