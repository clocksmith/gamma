def solve(text):
    counts = [0] * 26
    for character in text:
        counts[ord(character) - 97] += 1
    for index, character in enumerate(text):
        if counts[ord(character) - 97] == 1:
            return index
    return -1
