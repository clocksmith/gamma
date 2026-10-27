"""3973. Distinct Gate Paths to LCA
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/distinct-gate-paths-to-lca/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3973.Distinct%20Gate%20Paths%20to%20LCA/README_EN.md
Complexity: O((n+q) log n) time, O(n log n) space.
Exactly one gate is used per upward move; no gate at the LCA is consumed. Card 0 is blue, 1 red. Matrix products preserve upward order; exact modular multiplication in JavaScript. Inputs preserved; native method pending.
"""

from __future__ import annotations

def solve(n, parent, gates, queries):
    modulus = 1000000007
    children = [[] for _ in range(n)]
    for node in range(1, n):
        children[parent[node]].append(node)
    depth = [0] * n
    order = [0]
    for node in order:
        for child in children[node]:
            depth[child] = depth[node] + 1
            order.append(child)
    levels = n.bit_length()
    ancestor = [[0 if value < 0 else value for value in parent]]
    matrices = [[(blue, white, white, red) for red, blue, white in gates]]
    matrices[0][0] = (1, 0, 0, 1)
    def multiply(left, right):
        a, b, c, d = left
        e, f, g, h = right
        return ((a * e + b * g) % modulus, (a * f + b * h) % modulus,
                (c * e + d * g) % modulus, (c * f + d * h) % modulus)
    for level in range(1, levels):
        previous = ancestor[-1]
        old = matrices[-1]
        ancestor.append([previous[previous[node]] for node in range(n)])
        matrices.append([multiply(old[node], old[previous[node]]) for node in range(n)])
    def lift(node, vector, level):
        a, b, c, d = matrices[level][node]
        blue, red = vector
        return ancestor[level][node], ((blue * a + red * c) % modulus,
                                       (blue * b + red * d) % modulus)
    answer = 0
    for left, left_card, right, right_card in queries:
        left_vector = (1 - left_card, left_card)
        right_vector = (1 - right_card, right_card)
        if depth[left] < depth[right]:
            left, right = right, left
            left_vector, right_vector = right_vector, left_vector
        difference = depth[left] - depth[right]
        for level in range(levels):
            if (difference >> level) & 1:
                left, left_vector = lift(left, left_vector, level)
        if left != right:
            for level in range(levels - 1, -1, -1):
                if ancestor[level][left] != ancestor[level][right]:
                    left, left_vector = lift(left, left_vector, level)
                    right, right_vector = lift(right, right_vector, level)
            left, left_vector = lift(left, left_vector, 0)
            right, right_vector = lift(right, right_vector, 0)
        ways = (sum(left_vector) * sum(right_vector)) % modulus
        answer ^= ways
    return answer
