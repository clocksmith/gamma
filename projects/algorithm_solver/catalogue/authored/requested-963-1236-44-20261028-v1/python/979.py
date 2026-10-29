"""Original candidate; no qualification or admission."""

def solve(root):
    balances={};moves=0;stack=[(root,False)]
    while stack:
        n,seen=stack.pop()
        if n is None:continue
        if not seen:stack.extend([(n,True),(n.left,False),(n.right,False)]);continue
        left=balances.get(id(n.left),0);right=balances.get(id(n.right),0)
        moves+=abs(left)+abs(right);balances[id(n)]=n.val-1+left+right
    return moves


class Solution:
    def distributeCoins(self, root):
        return solve(root)
