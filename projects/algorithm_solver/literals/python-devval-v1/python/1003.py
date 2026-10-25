def solve(text):
    stack = []
    for character in text:
        stack.append(character)
        if len(stack) >= 3 and stack[-3:] == ["a", "b", "c"]:
            del stack[-3:]
    return not stack
