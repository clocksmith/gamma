"""Original candidate for LeetCode 2046. Contract: https://leetcode.com/problems/sort-linked-list-already-sorted-using-absolute-values/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
solve accepts native linked nodes (val,next), reorders links in place and preserves node identity; JSON array input is an explicit values-only serialization adapter returning a new array.
Complexity: O(n) time and space"""
def solve(head):
    if head is None:return None
    if not isinstance(head,list):
        previous=head;current=head.next
        while current is not None:
            following=current.next
            if current.val<0:
                previous.next=following;current.next=head;head=current
            else:previous=current
            current=following
        return head
    negative=[];positive=[]
    for x in head:
        (negative if x<0 else positive).append(x)
    return negative[::-1]+positive
