from collections import Counter


def solve(s, k):
    counts = Counter(s)
    middle = next((ch for ch, count in counts.items() if count % 2), '')
    half = [counts.get(chr(97 + i), 0) // 2 for i in range(26)]

    def combinations_capped(n, r, cap):
        value = 1
        for i in range(1, min(r, n - r) + 1):
            value = value * (n - i + 1) // i
            if value >= cap:
                return cap
        return value

    def arrangements(cap):
        ways, used = 1, 0
        for count in half:
            ways *= combinations_capped(used + count, count, cap)
            if ways >= cap:
                return cap
            used += count
        return ways

    if arrangements(k) < k:
        return ''
    prefix = []
    for _ in range(len(s) // 2):
        for letter in range(26):
            if half[letter] == 0:
                continue
            half[letter] -= 1
            ways = arrangements(k)
            if ways >= k:
                prefix.append(chr(97 + letter))
                break
            k -= ways
            half[letter] += 1
    left = ''.join(prefix)
    return left + middle + left[::-1]
