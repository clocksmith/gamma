class Solution:
    def flipMatchVoyage(self, root, voyage):
        stack = [root] if root is not None else []
        flipped = []
        index = 0
        while stack:
            node = stack.pop()
            if index == len(voyage) or node.val != voyage[index]:
                return [-1]
            index += 1
            left = node.left
            right = node.right
            if left is not None and (index == len(voyage) or left.val != voyage[index]):
                flipped.append(node.val)
                if left is not None:
                    stack.append(left)
                if right is not None:
                    stack.append(right)
            else:
                if right is not None:
                    stack.append(right)
                if left is not None:
                    stack.append(left)
        return flipped if index == len(voyage) else [-1]
