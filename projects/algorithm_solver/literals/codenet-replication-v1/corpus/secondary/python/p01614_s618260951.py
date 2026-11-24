from collections import defaultdict

max_phrases = defaultdict(int)
n = int(input())
for _ in range(n):
    s, l, p = map(int, input().split())
    for length in range(s, l + 1):
        max_phrases[length] = max(max_phrases[length], p)

m = int(input())
melodies = [int(input()) for _ in range(m)]

max_length = max(melodies)
dp = [-1] * (max_length + max(max_phrases))
dp[0] = 0

for i in range(max_length):
    c = dp[i]
    if c == -1:
        continue
    for length, p in max_phrases.items():
        dp[i + length] = max(dp[i + length], c + p)

results = [dp[melody] for melody in melodies]
print(-1 if -1 in results else '\n'.join(map(str, results)))