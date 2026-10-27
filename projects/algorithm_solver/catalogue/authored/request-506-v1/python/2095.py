# Original candidate implementation. Contract: https://leetcode.com/problems/delete-the-middle-node-of-a-linked-list/
def solve(head):
    if head.next is None:return None
    slow=fast=head;previous=None
    while fast is not None and fast.next is not None:
        previous=slow;slow=slow.next;fast=fast.next.next
    previous.next=slow.next
    return head
