"""3292. Minimum Number of Valid Strings to Form Target II: Aho-Corasick longest valid suffixes and prefix-closed segmentation."""


def solve(words: list[str], target: str) -> int:
    """O(26*S + T) time and O(26*S + T) auxiliary space. Inputs are preserved."""
    transitions = [[0] * 26]
    depth = [0]
    failure = [0]
    for word in words:
        node = 0
        for character in word:
            letter = ord(character) - ord('a')
            if transitions[node][letter] == 0:
                transitions[node][letter] = len(transitions)
                transitions.append([0] * 26)
                depth.append(depth[node] + 1)
                failure.append(0)
            node = transitions[node][letter]
    queue = [child for child in transitions[0] if child]
    head = 0
    while head < len(queue):
        node = queue[head]
        head += 1
        for letter in range(26):
            child = transitions[node][letter]
            if child:
                failure[child] = transitions[failure[node]][letter]
                queue.append(child)
            else:
                transitions[node][letter] = transitions[failure[node]][letter]
    best = [0] * (len(target) + 1)
    node = 0
    for end, character in enumerate(target, 1):
        node = transitions[node][ord(character) - ord('a')]
        length = depth[node]
        if length == 0:
            return -1
        # Prefix closure makes optimal prefix cost nondecreasing, so use the longest suffix.
        best[end] = best[end - length] + 1
    return best[-1]


class Solution:
    def minValidStrings(self, words: list[str], target: str) -> int:
        return solve(words, target)
