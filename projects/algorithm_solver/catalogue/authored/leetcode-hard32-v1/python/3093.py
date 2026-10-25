"""3093. Longest Common Suffix Queries."""

def solve(wordsContainer: list[str], wordsQuery: list[str]) -> list[int]:
    """Compact reverse trie: O(26*(S+Q)) time, O(S+query_count) space for total lengths S,Q."""
    first_child = [-1]
    next_sibling = [-1]
    symbol = ['']
    best = [-1]

    def find_child(node: int, char: str) -> int:
        child = first_child[node]
        while child != -1 and symbol[child] != char:
            child = next_sibling[child]
        return child

    for index, word in enumerate(wordsContainer):
        node = 0
        if best[0] == -1 or len(word) < len(wordsContainer[best[0]]):
            best[0] = index
        for char in reversed(word):
            child = find_child(node, char)
            if child == -1:
                child = len(first_child)
                first_child.append(-1)
                next_sibling.append(first_child[node])
                symbol.append(char)
                best.append(index)
                first_child[node] = child
            node = child
            if len(word) < len(wordsContainer[best[node]]):
                best[node] = index
    answer = []
    for word in wordsQuery:
        node = 0
        for char in reversed(word):
            child = find_child(node, char)
            if child == -1:
                break
            node = child
        answer.append(best[node])
    return answer


class Solution:
    def stringIndices(self, wordsContainer: list[str], wordsQuery: list[str]) -> list[int]:
        return solve(wordsContainer, wordsQuery)
