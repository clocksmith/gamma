"""1773. Count Items Matching a Rule (Easy).

Specification: https://leetcode.com/problems/count-items-matching-a-rule/description/
"""


INDEX = {'type': 0, 'color': 1, 'name': 2}


def solve(items: list[list[str]], ruleKey: str, ruleValue: str) -> int:
    index = INDEX[ruleKey]
    count = 0
    for item in items:
        if item[index] == ruleValue:
            count += 1
    return count


class Solution:
    def countMatches(self, items: list[list[str]], ruleKey: str, ruleValue: str) -> int:
        return solve(items, ruleKey, ruleValue)
