class TreeNode:
    def __init__(self):
        self.val=-1
        self.left=-1
        self.right=-1
        self.parent=-1

n=int(input())
nodes=[TreeNode() for _ in range(n)]

for _ in range(n):
    idx,left,right=map(int,input().split())
    nodes[idx].val=idx
    nodes[idx].left=left
    nodes[idx].right=right
    if(left!=-1):
        nodes[left].parent=idx
    if(right!=-1):
        nodes[right].parent=idx

root_idx=-1
for i in range(n):
    if(nodes[i].parent==-1):
        root_idx=i
        break

preorder_idx=[]
def preOrder(idx):
    preorder_idx.append(idx)
    if(nodes[idx].left!=-1):
        preOrder(nodes[idx].left)
    if(nodes[idx].right!=-1):
        preOrder(nodes[idx].right)

inorder_idx=[]
def inOrder(idx):
    if(nodes[idx].left!=-1):
        inOrder(nodes[idx].left)
    inorder_idx.append(idx)
    if(nodes[idx].right!=-1):
        inOrder(nodes[idx].right)

postorder_idx=[]
def postOrder(idx):
    if(nodes[idx].left!=-1):
        postOrder(nodes[idx].left)
    if(nodes[idx].right!=-1):
        postOrder(nodes[idx].right)
    postorder_idx.append(idx)


preOrder(root_idx)
inOrder(root_idx)
postOrder(root_idx)

print("Preorder")
print(" ",end="")
print(*preorder_idx)

print("Inorder")
print(" ",end="")
print(*inorder_idx)

print("Postorder")
print(" ",end="")
print(*postorder_idx)

