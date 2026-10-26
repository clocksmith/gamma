"""2977. Minimum Cost to Convert String II.

All-pairs conversion costs plus trie-guided prefix DP; O(U^3+n*L+S) time, O(U^2+n+S) space. Inputs are preserved.
"""

def solve(source: str, target: str, original: list[str], changed: list[str], cost: list[int]) -> int:
    words = list(dict.fromkeys(original + changed))
    identity = {word: index for index, word in enumerate(words)}
    size = len(words)
    distance = [[float('inf')] * size for _ in words]
    for index in range(size):
        distance[index][index] = 0
    for first, second, price in zip(original, changed, cost):
        a, b = identity[first], identity[second]
        distance[a][b] = min(distance[a][b], price)
    for middle in range(size):
        for a in range(size):
            if distance[a][middle] == float('inf'):
                continue
            for b in range(size):
                distance[a][b] = min(distance[a][b], distance[a][middle] + distance[middle][b])
    children, terminal = [{}], [-1]
    for word, index in identity.items():
        state = 0
        for char in word:
            if char not in children[state]:
                children[state][char] = len(children)
                children.append({})
                terminal.append(-1)
            state = children[state][char]
        terminal[state] = index
    best = [0] + [float('inf')] * len(source)
    for start in range(len(source)):
        if best[start] == float('inf'):
            continue
        if source[start] == target[start]:
            best[start + 1] = min(best[start + 1], best[start])
        a = b = 0
        for end in range(start, len(source)):
            a = children[a].get(source[end], -1)
            b = children[b].get(target[end], -1)
            if a == -1 or b == -1:
                break
            if terminal[a] != -1 and terminal[b] != -1:
                best[end + 1] = min(best[end + 1], best[start] + distance[terminal[a]][terminal[b]])
    return -1 if best[-1] == float('inf') else best[-1]


class Solution:
    def minimumCost(self, source: str, target: str, original: list[str], changed: list[str], cost: list[int]) -> int:
        return solve(source, target, original, changed, cost)
