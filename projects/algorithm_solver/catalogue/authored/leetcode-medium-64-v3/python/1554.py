"""1554. Strings Differ by One Character: identify exact prefix and suffix pairs with trie-state identities."""


def solve(dict: list[str]) -> bool:
    """O(S) expected time and O(S) space for S total characters; no probabilistic hashes; inputs are read-only."""
    prefix_edges = {}
    suffix_edges = {}
    removed = {}
    for word in dict:
        suffixes = [0] * (len(word) + 1)
        for index in range(len(word) - 1, -1, -1):
            transition = (suffixes[index + 1], word[index])
            state = suffix_edges.get(transition)
            if state is None:
                state = len(suffix_edges) + 1
                suffix_edges[transition] = state
            suffixes[index] = state
        prefix = 0
        for index, char in enumerate(word):
            signature = (prefix, suffixes[index + 1])
            previous = removed.get(signature)
            if previous is not None and previous != char:
                return True
            removed[signature] = char
            transition = (prefix, char)
            state = prefix_edges.get(transition)
            if state is None:
                state = len(prefix_edges) + 1
                prefix_edges[transition] = state
            prefix = state
    return False


class Solution:
    def differByOne(self, dict: list[str]) -> bool:
        return solve(dict)
