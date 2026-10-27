"""3758. Convert Number Words to Digits
Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
Signature: solve(s).
Algorithm: Scan left to right for one of ten bounded-length words, consuming an entire matched word.
Complexity: O(n) time; O(n) output space.
Numeric semantics: Exact integer arithmetic on the published input bounds; JavaScript Number results remain safe integers.
Mutation: Does not mutate input arrays, rows, strings, or trees.
Interface: Ordered-positional solve; native forwarding name included only when confirmed.
Specification: https://leetcode.com/problems/convert-number-words-to-digits/description/
Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3758.Convert%20Number%20Words%20to%20Digits/README_EN.md
Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
New readable implementations; no third-party source bodies copied verbatim.
No protected tests or private reference implementations used.
"""

def solve(s):
    words = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine")
    digits = []
    index = 0
    while index < len(s):
        for digit, word in enumerate(words):
            if s.startswith(word, index):
                digits.append(str(digit))
                index += len(word)
                break
        else:
            index += 1
    return "".join(digits)


def convertNumber(s):
    return solve(s)


class Solution:
    def convertNumber(self, s):
        return solve(s)
