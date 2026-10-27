"""4077. Minimize Inversions in a Prefix Tree
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/minimize-inversions-in-a-prefix-tree/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4077.Minimize%20Inversions%20in%20a%20Prefix%20Tree/README_EN.md
Complexity: O(10L + sum_v d_v*2^d_v) time, O(L + sum_v d_v^2 + 10*2^10) space; L total word length, d_v<=10.
A pair in different child subtrees is charged once at its LCA. Child ordering costs depend only on subtree rank sets, so each branching node is optimized independently with subset DP. Marked-prefix/descendant pairs have fixed preorder and are counted separately. Inputs preserved.
"""

from __future__ import annotations

def solve(words, target):
    children = [{}]
    for word in words:
        node = 0
        for character in word:
            entry = children[node].get(character)
            if entry is None:
                entry = (len(children), len(children[node]))
                children[node][character] = entry
                children.append({})
            node = entry[0]
    degrees = [len(child) for child in children]
    seen = [[0]*d if d > 1 else None for d in degrees]
    cross = [[0]*(d*d) if d > 1 else None for d in degrees]
    total = [0]*len(children)
    answer = 0
    # Earlier target positions have smaller rank. Charge every pair at its LCA.
    for word_index in target:
        node = 0
        for character in words[word_index]:
            child, branch = children[node][character]
            d = degrees[node]
            if d > 1:
                for other in range(d):
                    if other != branch:
                        cross[node][branch*d+other] += seen[node][other]
                seen[node][branch] += 1
            total[node] += 1
            node = child
        # This marked prefix must be visited before every marked descendant.
        answer += total[node]
        total[node] += 1
    for node, d in enumerate(degrees):
        if d < 2:
            continue
        costs = cross[node]
        if d == 2:
            answer += min(costs[1], costs[2])
            continue
        size = 1 << d
        incoming = [[0]*size for _ in range(d)]
        for last in range(d):
            row = incoming[last]
            for mask in range(1, size):
                low = mask & -mask
                first = low.bit_length()-1
                row[mask] = row[mask-low]+costs[first*d+last]
        best = [float('inf')]*size
        best[0] = 0
        for mask in range(1, size):
            bits = mask
            while bits:
                low = bits & -bits
                last = low.bit_length()-1
                previous = mask-low
                best[mask] = min(best[mask], best[previous]+incoming[last][previous])
                bits -= low
        answer += best[-1]
    return answer
