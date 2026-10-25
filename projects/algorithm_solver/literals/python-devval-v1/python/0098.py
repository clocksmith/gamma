def solve(root):
    stack = []
    current = root
    previous = None
    has_previous = False
    while current is not None or stack:
        while current is not None:
            stack.append(current)
            current = current.left
        current = stack.pop()
        if has_previous and current.val <= previous:
            return False
        previous = current.val
        has_previous = True
        current = current.right
    return True
