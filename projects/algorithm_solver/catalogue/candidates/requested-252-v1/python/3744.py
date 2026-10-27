"""3744. Find Kth Character in Expanded String
Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
Signature: solve(s, k).
Algorithm: Subtract run lengths without materializing the expansion; reset repetition rank after spaces.
Complexity: O(length of s) time; O(1) auxiliary space.
Numeric semantics: Exact integer arithmetic on the published input bounds; JavaScript Number results remain safe integers.
Mutation: Does not mutate input arrays, rows, strings, or trees.
Interface: Ordered-positional solve; native forwarding name included only when confirmed.
Specification: https://leetcode.com/problems/find-kth-character-in-expanded-string/description/
Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3744.Find%20Kth%20Character%20in%20Expanded%20String/README_EN.md
Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
New readable implementations; no third-party source bodies copied verbatim.
No protected tests or private reference implementations used.
Contract note: Each space remains one character; k can exceed 32 bits, so no bitwise indexing is used.
"""

def solve(s, k):
    position = 0
    for character in s:
        if character == " ":
            repetitions = 1
            position = 0
        else:
            position += 1
            repetitions = position
        if k < repetitions:
            return character
        k -= repetitions
    raise ValueError("k is outside the expanded string.")


def kthCharacter(s, k):
    return solve(s, k)


class Solution:
    def kthCharacter(self, s, k):
        return solve(s, k)
