a, b = map(lambda x: int(x), input().split())

lis = [a+b, a-b, a*b]
print(max(lis))