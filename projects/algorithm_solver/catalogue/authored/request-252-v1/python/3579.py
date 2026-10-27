def solve(word1, word2):
    n = len(word1)
    first = [ord(character) - 97 for character in word1]
    second = [ord(character) - 97 for character in word2]

    def cost(left, right, reverse):
        unmatched = {}
        operations = int(reverse)
        for offset in range(right - left + 1):
            a = first[right - offset if reverse else left + offset]
            b = second[left + offset]
            if a == b:
                continue
            opposite = b * 26 + a
            if unmatched.get(opposite, 0):
                # Two opposite mismatches use one swap rather than two replacements.
                unmatched[opposite] -= 1
            else:
                key = a * 26 + b
                unmatched[key] = unmatched.get(key, 0) + 1
                operations += 1
        return operations

    best = [0] + [n + 1] * n
    for end in range(1, n + 1):
        for start in range(end):
            edits = min(cost(start, end - 1, False), cost(start, end - 1, True))
            best[end] = min(best[end], best[start] + edits)
    return best[n]
