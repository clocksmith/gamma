def solve(text):
    closing = {"(": ")", "[": "]", "{": "}"}
    stack = []
    for character in text:
        if character in closing:
            stack.append(closing[character])
        elif not stack or stack.pop() != character:
            return False
    return not stack
