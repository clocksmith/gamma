# Original candidate; contract and evidence: ../batch1/manifest.json
def solve(s, k):
    lengths = [0]
    for letter in s:
        length = lengths[-1]
        if letter == '*':
            length = max(0, length - 1)
        elif letter == '#':
            length *= 2
        elif letter != '%':
            length += 1
        lengths.append(length)
    if k >= lengths[-1]:
        return '.'
    for index in range(len(s) - 1, -1, -1):
        letter, before = s[index], lengths[index]
        if letter == '#':
            k %= before
        elif letter == '%':
            k = before - 1 - k
        elif letter != '*' and k == before:
            return letter
    return '.'
