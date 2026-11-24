while True:
    n = int(input())
    if n == 0:
        break
    
    [print("{} {}".format(max(x), min(x))) for x in [[sum(map(int, input().split())) for i in range(n)]]]