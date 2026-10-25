def solve(first, second):
    pending = [(first, second)]
    while pending:
        left, right = pending.pop()
        if left is None or right is None:
            if left is not right:
                return False
        else:
            if left.val != right.val:
                return False
            pending.append((left.right, right.right))
            pending.append((left.left, right.left))
    return True
