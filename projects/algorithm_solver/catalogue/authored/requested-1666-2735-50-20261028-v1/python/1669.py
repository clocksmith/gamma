"""Original candidate; no qualification or admission."""

class ListNode:
    def __init__(self,val=0,next=None):self.val,self.next=val,next

def solve(list1,a,b,list2):
    dummy=ListNode();tail=dummy;node=list1;index=0
    while node is not None:
        if index==a:
            other=list2
            while other is not None:tail.next=ListNode(other.val);tail=tail.next;other=other.next
        if index<a or index>b:tail.next=ListNode(node.val);tail=tail.next
        node=node.next;index+=1
    return dummy.next


class Solution:
    def mergeInBetween(self, list1, a, b, list2):
        return solve(list1, a, b, list2)
