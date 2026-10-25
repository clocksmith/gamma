def solve(parentheses):
    unmatched_open = 0
    missing_open = 0
    for character in parentheses:
        if character == "(":
            unmatched_open += 1
        elif unmatched_open:
            unmatched_open -= 1
        else:
            missing_open += 1
    return unmatched_open + missing_open
