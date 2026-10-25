def solve(operations):
    scores = []
    for operation in operations:
        if operation == "+":
            scores.append(scores[-1] + scores[-2])
        elif operation == "D":
            scores.append(2 * scores[-1])
        elif operation == "C":
            scores.pop()
        else:
            scores.append(int(operation))
    return sum(scores)
