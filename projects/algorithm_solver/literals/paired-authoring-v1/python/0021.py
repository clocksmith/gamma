# External ListNode shape: val: int, next: ListNode | None.
class Link:
    def __init__(self, next_node=None):
        self.next = next_node


class Solution:
    def mergeTwoLists(self, list1, list2):
        sentinel = Link()
        tail = sentinel
        while list1 is not None and list2 is not None:
            if list1.val <= list2.val:
                tail.next = list1
                list1 = list1.next
            else:
                tail.next = list2
                list2 = list2.next
            tail = tail.next

        if list1 is not None:
            tail.next = list1
        else:
            tail.next = list2
        return sentinel.next
