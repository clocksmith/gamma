"""Original candidate; no qualification or admission."""

def solve(head):
    out=[];stack=[];node=head
    while node is not None:
        at=len(out);out.append(0)
        while stack and stack[-1][1]<node.val:out[stack.pop()[0]]=node.val
        stack.append((at,node.val));node=node.next
    return out


class Solution:
    def nextLargerNodes(self, head):
        return solve(head)
