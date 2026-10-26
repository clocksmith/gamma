"""3606. Coupon Code Validator (Easy).

Specification: https://leetcode.com/problems/coupon-code-validator/description/
"""


def solve(code: list[str], businessLine: list[str], isActive: list[bool]) -> list[str]:
    """O(n * L * log(n + 1)) time, O(n) reference space; ASCII ordering; preserve inputs."""
    categories = ['electronics', 'grocery', 'pharmacy', 'restaurant']
    groups = [[] for _ in categories]
    for index, value in enumerate(code):
        if not isActive[index] or businessLine[index] not in categories or not value:
            continue
        valid = True
        for character in value:
            if not ('a' <= character <= 'z' or 'A' <= character <= 'Z'
                    or '0' <= character <= '9' or character == '_'):
                valid = False
                break
        if valid:
            groups[categories.index(businessLine[index])].append(value)
    result = []
    for group in groups:
        group.sort()
        result.extend(group)
    return result


class Solution:
    def validateCoupons(
        self,
        code: list[str],
        businessLine: list[str],
        isActive: list[bool],
    ) -> list[str]:
        return solve(code, businessLine, isActive)
