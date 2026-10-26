"""1948. Delete Duplicate Folders in System: bottom-up structural interning followed by simultaneous deletion."""


def solve(paths: list[list[str]]) -> list[list[str]]:
    """O(S + N*log N + output size) time and O(S + N + output size) space. Inputs are preserved."""
    children = [{}]
    for path in paths:
        node = 0
        for name in path:
            if name not in children[node]:
                children[node][name] = len(children)
                children.append({})
            node = children[node][name]
    shape = [0] * len(children)
    interned = {}
    frequency = [0]
    for node in range(len(children) - 1, 0, -1):
        if not children[node]:
            continue
        signature = tuple(sorted((name, shape[child]) for name, child in children[node].items()))
        if signature not in interned:
            interned[signature] = len(frequency)
            frequency.append(0)
        shape[node] = interned[signature]
        frequency[shape[node]] += 1
    answer = []
    stack = [(0, [])]
    while stack:
        node, path = stack.pop()
        if node and shape[node] and frequency[shape[node]] > 1:
            continue
        if node:
            answer.append(path)
        for name, child in sorted(children[node].items(), reverse=True):
            stack.append((child, path + [name]))
    return answer


class Solution:
    def deleteDuplicateFolder(self, paths: list[list[str]]) -> list[list[str]]:
        return solve(paths)
