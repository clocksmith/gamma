def solve(complexity):
    answer = 1
    for i in range(1, len(complexity)):
        if complexity[i] <= complexity[0]:
            return 0
        answer = answer * i % 1_000_000_007
    return answer
