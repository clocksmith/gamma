"""3706. Maximum Distance Between Unequal Words in Array II
Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
Signature: solve(words).
Algorithm: An optimal unequal pair touches an array endpoint; compare each word to both endpoints.
Complexity: O(n * maximum word length) time; O(1) auxiliary space.
Numeric semantics: Exact integer arithmetic on the published input bounds; JavaScript Number results remain safe integers.
Mutation: Does not mutate input arrays, rows, strings, or trees.
Interface: Ordered-positional solve; native forwarding name included only when confirmed.
Specification: https://leetcode.com/problems/maximum-distance-between-unequal-words-in-array-ii/description/
Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3706.Maximum%20Distance%20Between%20Unequal%20Words%20in%20Array%20II/README_EN.md
Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
New readable implementations; no third-party source bodies copied verbatim.
No protected tests or private reference implementations used.
Contract note: Distance is j - i + 1, not j - i. Identical words throughout return 0.
"""

def solve(words):
    count = len(words)
    answer = 0
    for index, word in enumerate(words):
        if word != words[0]:
            answer = max(answer, index + 1)
        if word != words[-1]:
            answer = max(answer, count - index)
    return answer


def maxDistance(words):
    return solve(words)


class Solution:
    def maxDistance(self, words):
        return solve(words)
