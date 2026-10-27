"""3662. Filter Characters by Frequency
Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
Signature: solve(s, k).
Algorithm: Count globally, then filter in original order.
Complexity: O(n) time; O(n) output space and O(26) counting space.
Numeric semantics: Exact integer arithmetic on the published input bounds; JavaScript Number results remain safe integers.
Mutation: Does not mutate input arrays, rows, strings, or trees.
Interface: Ordered-positional solve; native forwarding name included only when confirmed.
Specification: https://leetcode.com/problems/filter-characters-by-frequency/description/
Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3600-3699/3662.Filter%20Characters%20by%20Frequency/README_EN.md
Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
New readable implementations; no third-party source bodies copied verbatim.
No protected tests or private reference implementations used.
"""

def solve(s, k):
    counts = [0] * 26
    for letter in s:
        counts[ord(letter) - ord("a")] += 1
    return "".join(letter for letter in s if counts[ord(letter) - ord("a")] < k)


def filterCharacters(s, k):
    return solve(s, k)


class Solution:
    def filterCharacters(self, s, k):
        return solve(s, k)
