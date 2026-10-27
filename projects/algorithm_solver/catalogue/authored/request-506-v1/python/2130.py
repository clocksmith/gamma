# Original candidate implementation. Contract: https://leetcode.com/problems/maximum-twin-sum-of-a-linked-list/
def solve(head):
    values=[]
    while head is not None:values.append(head.val);head=head.next
    return max(values[i]+values[-1-i] for i in range(len(values)//2))
