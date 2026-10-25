def solve(words):
    deleted = 0
    for column in range(len(words[0])):
        for row in range(1, len(words)):
            if words[row - 1][column] > words[row][column]:
                deleted += 1
                break
    return deleted
