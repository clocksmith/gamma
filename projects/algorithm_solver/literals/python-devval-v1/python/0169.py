def solve(values):
    candidate = 0
    balance = 0
    for value in values:
        if balance == 0:
            candidate = value
        balance += 1 if value == candidate else -1
    return candidate
