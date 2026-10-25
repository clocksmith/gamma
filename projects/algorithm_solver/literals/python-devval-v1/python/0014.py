def solve(words):
    first = words[0]
    length = len(first)
    for word in words[1:]:
        length = min(length, len(word))
        index = 0
        while index < length and first[index] == word[index]:
            index += 1
        length = index
    return first[:length]
