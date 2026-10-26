"""3062. Winner of the Linked List Game (Easy).

Specification: https://leetcode.com/problems/winner-of-the-linked-list-game/description/
"""


def solve(head) -> str:
    """O(n) time, O(1) space; compare consecutive pairs in the even-length list without mutation."""
    score_difference = 0
    current = head
    while current is not None:
        partner = current.next
        if current.val > partner.val:
            score_difference += 1
        if current.val < partner.val:
            score_difference -= 1
        current = partner.next
    if score_difference > 0:
        return 'Even'
    if score_difference < 0:
        return 'Odd'
    return 'Tie'


class Solution:
    def gameResult(self, head) -> str:
        return solve(head)
