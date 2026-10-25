def solve(text, queries):
    parity = [0]
    for character in text:
        parity.append(parity[-1] ^ (1 << (ord(character) - 97)))
    result = []
    for left, right, changes in queries:
        odd = (parity[right + 1] ^ parity[left]).bit_count()
        result.append(odd // 2 <= changes)
    return result
