class TreeNode:
    def __init__(self, value, left=None, right=None):
        self.val = value
        self.left = left
        self.right = right


def solve(head):
    values = []
    while head is not None:
        values.append(head.val)
        head = head.next

    def build(low, high):
        if low > high:
            return None
        middle = (low + high) // 2
        return TreeNode(values[middle], build(low, middle - 1), build(middle + 1, high))

    return build(0, len(values) - 1)
