"""648. Replace Words."""

def solve(dictionary: list[str], sentence: str) -> str:
    trie = {}
    for root in dictionary:
        node = trie
        for char in root:
            node = node.setdefault(char, {})
        node[''] = True
    answer = []
    for word in sentence.split(' '):
        node = trie
        replacement = word
        for i, char in enumerate(word):
            if char not in node:
                break
            node = node[char]
            if '' in node:
                replacement = word[:i + 1]
                break
        answer.append(replacement)
    return ' '.join(answer)


class Solution:
    def replaceWords(self, dictionary: list[str], sentence: str) -> str:
        return solve(dictionary, sentence)
