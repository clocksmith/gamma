"""3045. Count Prefix and Suffix Pairs II.

Trie of paired forward/reverse letters counts earlier complete words; O(total characters) expected time and space. Inputs are preserved.
"""

def solve(words: list[str]) -> int:
    children, terminal = [{}], [0]
    answer = 0
    for word in words:
        state = 0
        for index, char in enumerate(word):
            pair = (ord(char) - 97) * 26 + ord(word[-1 - index]) - 97
            if pair not in children[state]:
                children[state][pair] = len(children)
                children.append({})
                terminal.append(0)
            state = children[state][pair]
            answer += terminal[state]
        terminal[state] += 1
    return answer


class Solution:
    def countPrefixSuffixPairs(self, words: list[str]) -> int:
        return solve(words)
