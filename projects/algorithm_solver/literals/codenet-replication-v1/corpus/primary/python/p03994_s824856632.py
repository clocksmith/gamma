s = input()
k = int(input())

alph = "abcdefghijklmnopqrstuvwxyz"
memo = {}
for i, char in enumerate(alph):
    memo[char] = 26 - i
memo["a"] = 0

ans = []
for char in s:
    if memo[char] <= k:
        ans.append("a")
        k -= memo[char]
    else:
        ans.append(char)
ans[-1] = alph[(26 - memo[ans[-1]] + k) % 26]
print("".join(map(str, ans)))