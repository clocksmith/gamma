def solve(parentheses):
    depth = 0
    score = 0
    previous = ""
    for character in parentheses:
        if character == "(":
            depth += 1
        else:
            depth -= 1
            if previous == "(":
                score += 1 << depth
        previous = character
    return score
