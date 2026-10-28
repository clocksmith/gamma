"""966. Vowel Spellchecker (Medium).

Specification: https://leetcode.com/problems/vowel-spellchecker/description/
"""


def _vowel_key(word):
    return "".join('*' if ch in 'aeiou' else ch for ch in word)


def solve(wordlist: list[str], queries: list[str]) -> list[str]:
    exact = set(wordlist)
    lower_map = {}
    vowel_map = {}
    for word in wordlist:
        lower = word.lower()
        if lower not in lower_map:
            lower_map[lower] = word
        key = _vowel_key(lower)
        if key not in vowel_map:
            vowel_map[key] = word
    result = []
    for query in queries:
        if query in exact:
            result.append(query)
        else:
            lower = query.lower()
            if lower in lower_map:
                result.append(lower_map[lower])
            elif _vowel_key(lower) in vowel_map:
                result.append(vowel_map[_vowel_key(lower)])
            else:
                result.append('')
    return result


class Solution:
    def spellchecker(self, wordlist: list[str], queries: list[str]) -> list[str]:
        return solve(wordlist, queries)
