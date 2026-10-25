def solve(text, goal):
    if len(text) != len(goal) or not text:
        return False
    prefix = [0] * len(goal)
    matched = 0
    for index in range(1, len(goal)):
        while matched and goal[index] != goal[matched]:
            matched = prefix[matched - 1]
        if goal[index] == goal[matched]:
            matched += 1
        prefix[index] = matched
    matched = 0
    for index in range(2 * len(text) - 1):
        character = text[index % len(text)]
        while matched and character != goal[matched]:
            matched = prefix[matched - 1]
        if character == goal[matched]:
            matched += 1
        if matched == len(goal):
            return True
    return False
