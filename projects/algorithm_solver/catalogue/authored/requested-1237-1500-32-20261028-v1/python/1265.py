"""Original frontend 1265 variant; qualification unknown."""


def solve(head):
    if isinstance(head, list):
        return list(reversed(head))
    stack = []
    cur = head
    while cur is not None:
        stack.append(cur)
        cur = cur.getNext()
    while stack:
        stack.pop().printValue()
    return None


printLinkedListInReverse = solve


class Solution:
    def printLinkedListInReverse(self, head):
        return solve(head)
