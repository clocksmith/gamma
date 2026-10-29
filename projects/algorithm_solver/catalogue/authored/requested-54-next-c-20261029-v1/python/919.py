class CBTInserter:
    def __init__(self, root):
        self.nodes = [TreeNode(root.val)]
        originals = [root]
        for source,node in zip(originals,self.nodes):
            if source.left is not None:
                node.left = TreeNode(source.left.val)
                originals.append(source.left)
                self.nodes.append(node.left)
            if source.right is not None:
                node.right = TreeNode(source.right.val)
                originals.append(source.right)
                self.nodes.append(node.right)

    def insert(self, val):
        index = len(self.nodes)
        parent = self.nodes[(index-1)//2]
        child = TreeNode(val)
        if index % 2:
            parent.left = child
        else:
            parent.right = child
        self.nodes.append(child)
        return parent.val

    def get_root(self):
        return self.nodes[0]
