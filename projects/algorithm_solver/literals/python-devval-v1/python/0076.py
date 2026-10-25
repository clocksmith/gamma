def solve(text, required):
    counts = {}
    for character in required:
        counts[character] = counts.get(character, 0) + 1
    missing = len(required)
    left = 0
    best_start = 0
    best_length = len(text) + 1
    for right, character in enumerate(text):
        if character in counts:
            if counts[character] > 0:
                missing -= 1
            counts[character] -= 1
        while missing == 0:
            if right - left + 1 < best_length:
                best_start = left
                best_length = right - left + 1
            outgoing = text[left]
            left += 1
            if outgoing in counts:
                counts[outgoing] += 1
                if counts[outgoing] > 0:
                    missing += 1
    return "" if best_length > len(text) else text[best_start:best_start + best_length]
