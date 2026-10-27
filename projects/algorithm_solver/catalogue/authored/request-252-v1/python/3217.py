class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def modifiedList(nums, head):
    """Native API: retain survivor identities and rewire their next pointers."""
    removed = set(nums)
    dummy = ListNode(next=head)
    previous = dummy
    while previous.next is not None:
        if previous.next.val in removed:
            previous.next = previous.next.next
        else:
            previous = previous.next
    return dummy.next


def solve(nums, head_values):
    """JSON adapter: construct a fresh list; return survivor values."""
    head = None
    for value in reversed(head_values):
        head = ListNode(value, head)
    node = modifiedList(nums, head)
    result = []
    while node is not None:
        result.append(node.val)
        node = node.next
    return result
