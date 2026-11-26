n, d = map(int, input().split())
lst = list(map(int, input().split()))
ans = sum([x - d for x in lst if x - d >= 0])
print(ans if ans else "kusoge")
