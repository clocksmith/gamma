"""3846. Total Distance to Type a String Using One Finger
Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
Signature: solve(s).
Algorithm: Sum Manhattan distances on the specified left-aligned QWERTY grid, starting at a.
Complexity: O(n) time; O(26) space.
Numeric semantics: Exact integer arithmetic on the published input bounds; JavaScript Number results remain safe integers.
Mutation: Does not mutate input arrays, rows, strings, or trees.
Interface: Ordered-positional solve; native forwarding name included only when confirmed.
Specification: https://leetcode.com/problems/total-distance-to-type-a-string-using-one-finger/description/
Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3800-3899/3846.Total%20Distance%20to%20Type%20a%20String%20Using%20One%20Finger/README_EN.md
Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
New readable implementations; no third-party source bodies copied verbatim.
No protected tests or private reference implementations used.
"""

def solve(s):
    positions = {}
    for row, keys in enumerate(("qwertyuiop", "asdfghjkl", "zxcvbnm")):
        for column, key in enumerate(keys):
            positions[key] = (row, column)
    previous_row, previous_column = positions["a"]
    distance = 0
    for key in s:
        row, column = positions[key]
        distance += abs(row - previous_row) + abs(column - previous_column)
        previous_row, previous_column = row, column
    return distance


def totalDistance(s):
    return solve(s)


class Solution:
    def totalDistance(self, s):
        return solve(s)
