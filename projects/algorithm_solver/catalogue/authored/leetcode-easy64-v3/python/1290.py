"""1290. Convert Binary Number in a Linked List to Integer (Easy).

Specification: https://leetcode.com/problems/convert-binary-number-in-a-linked-list-to-integer/description/
"""


def solve(head) -> int:
    """O(n) time, O(1) space; preserve all input nodes and links."""
    result = 0
    node = head
    while node is not None:
        result = result * 2 + node.val
        node = node.next
    return result


class Solution:
    def getDecimalValue(self, head) -> int:
        return solve(head)
