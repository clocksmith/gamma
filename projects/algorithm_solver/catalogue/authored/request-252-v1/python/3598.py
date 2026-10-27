def solve(words):
    n = len(words)

    def lcp(a, b):
        length = 0
        while length < min(len(a), len(b)) and a[length] == b[length]:
            length += 1
        return length

    adjacent = [lcp(words[i], words[i + 1]) for i in range(n - 1)]
    prefix = [0] * n
    suffix = [0] * n
    for i, value in enumerate(adjacent):
        prefix[i + 1] = max(prefix[i], value)
    for i in range(n - 2, -1, -1):
        suffix[i] = max(suffix[i + 1], adjacent[i])
    answer = []
    for i in range(n):
        unaffected = max(prefix[max(0, i - 1)], suffix[min(n - 1, i + 1)])
        bridge = lcp(words[i - 1], words[i + 1]) if 0 < i < n - 1 else 0
        answer.append(max(unaffected, bridge))
    return answer
