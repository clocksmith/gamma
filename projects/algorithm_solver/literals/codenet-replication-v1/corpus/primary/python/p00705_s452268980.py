
while True:
    tmp = input().split(' ')
    n = int(tmp[0])
    q = int(tmp[1])
    if n == 0 and q == 0:
        break
    a = []
    d = [0]*100
    for i in range(n):
        a = input().split(' ')
        for j in range(int(a[0])):
            qq = int(a[ j+1 ])
            d[qq] = d[qq] + 1
    mx = max(d)
    if mx < q:
        print(0)
    else:
        for i in range(len(d)):
            if mx == d[i]:
                print( i )
                break