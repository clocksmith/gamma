n = int(input())

a = list(map(int,input().split()))

s = [0]*n
for i,a_n in enumerate(a):
    s[a_n-1] = i+1

p=""
for b in s:
    p += str(b) + " "

print(str(p[:-1]))