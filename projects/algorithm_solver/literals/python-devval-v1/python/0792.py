def solve(text, words):
    waiting = {}
    matched = 0
    for word in words:
        if word:
            waiting.setdefault(word[0], []).append((word, 1))
        else:
            matched += 1
    for character in text:
        pending = waiting.pop(character, [])
        for word, next_index in pending:
            if next_index == len(word):
                matched += 1
            else:
                waiting.setdefault(word[next_index], []).append((word, next_index + 1))
    return matched
