n, k = map(int, input().split())
l = list(range(1, n+1))

for i in range(k):
    okashi = int(input())
    people = list(map(int, input().split()))
    for num in people:
        if num in l:
            l.remove(num)

print(len(l))