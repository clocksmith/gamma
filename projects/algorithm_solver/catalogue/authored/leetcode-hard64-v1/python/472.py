"""472. Concatenated Words: shorter-word trie and segmentation dynamic programming."""


def solve(words: list[str]) -> list[str]:
    """O(sum(length^2)) time and O(total characters) auxiliary space. Inputs are preserved."""
    children = [{}]
    terminal = [False]
    concatenated = set()
    for word in sorted(words, key=len):
        if not word:
            continue
        pieces = [-1] * (len(word) + 1)
        pieces[0] = 0
        for start in range(len(word)):
            if pieces[start] < 0:
                continue
            node = 0
            for end in range(start, len(word)):
                node = children[node].get(word[end], -1)
                if node < 0:
                    break
                if terminal[node]:
                    pieces[end + 1] = max(pieces[end + 1], pieces[start] + 1)
        if pieces[-1] >= 2:
            concatenated.add(word)
        node = 0
        for character in word:
            if character not in children[node]:
                children[node][character] = len(children)
                children.append({})
                terminal.append(False)
            node = children[node][character]
        terminal[node] = True
    return [word for word in words if word in concatenated]


class Solution:
    def findAllConcatenatedWordsInADict(self, words: list[str]) -> list[str]:
        return solve(words)
