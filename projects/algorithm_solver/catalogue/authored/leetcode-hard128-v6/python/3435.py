"""3435. Frequencies of Shortest Supersequences.

Duplicate a minimum vertex subset so the remaining precedence graph is acyclic; O(2^d*d^2) time plus output and O(d^2) working space, d<=16. Inputs are preserved.
"""

def solve(words: list[str]) -> list[list[int]]:
    letters = sorted(set(''.join(words)))
    rank = {character: index for index, character in enumerate(letters)}
    size = len(letters)
    incoming = [0] * size
    forced = 0
    for word in words:
        first, second = rank[word[0]], rank[word[1]]
        incoming[second] |= 1 << first
        if first == second:
            forced |= 1 << first
    full = (1 << size) - 1
    best, answers = size + 1, []
    for duplicated in range(1 << size):
        amount = duplicated.bit_count()
        if amount > best or duplicated & forced != forced:
            continue
        remaining = full ^ duplicated
        while remaining:
            available = remaining
            removed = False
            while available:
                bit = available & -available
                available ^= bit
                node = bit.bit_length() - 1
                if incoming[node] & remaining == 0:
                    remaining ^= bit
                    removed = True
                    break
            if not removed:
                break
        if remaining:
            continue
        if amount < best:
            best, answers = amount, []
        counts = [0] * 26
        for index, character in enumerate(letters):
            counts[ord(character) - 97] = 1 + ((duplicated >> index) & 1)
        answers.append(counts)
    return answers


class Solution:
    def supersequences(self, words: list[str]) -> list[list[int]]:
        return solve(words)
