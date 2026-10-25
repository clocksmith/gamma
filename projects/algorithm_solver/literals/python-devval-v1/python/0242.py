def solve(first, second):
    counts = {}
    for character in first:
        counts[character] = counts.get(character, 0) + 1
    for character in second:
        counts[character] = counts.get(character, 0) - 1
    return all(count == 0 for count in counts.values())
