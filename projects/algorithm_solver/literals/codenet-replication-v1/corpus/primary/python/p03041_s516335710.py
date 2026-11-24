hoge = input().split()
s = input()
n = int(hoge[0])
k = int(hoge[1])
new_s = s[:k-1] + s[k-1].lower() + s[k:]
print(new_s)