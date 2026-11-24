import sys

s = input()
n = len(s)

# xxとxoxだけ見ればいい

for i in range(n - 1):
    if s[i] == s[i + 1]:
        print(i + 1, i + 2)
        sys.exit()

for i in range(n - 2):
    if s[i] == s[i + 2]:
        print(i + 1, i + 3)
        sys.exit()

print(-1, -1)