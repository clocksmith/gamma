"""725. Split Linked List in Parts. Cut original next links into k parts; earlier parts receive the extra nodes."""

def solve(head, k):
    length = 0
    node = head
    while node:
        length += 1
        node = node.next
    base, extra = divmod(length, k)
    answer = []
    node = head
    for part in range(k):
        size = base + (part < extra)
        answer.append(node)
        previous = None
        for _ in range(size):
            previous = node
            node = node.next
        if previous:
            previous.next = None
    return answer


class Solution:
    def splitListToParts(self, head, k):
        return solve(head, k)
