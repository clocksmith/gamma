while True:
    n,l,r = map(int, input().split())
    if n==0 and l==0 and r==0:
        break
    a = [0]*n
    cnt = 0
    for i in range(n):
        a[i]=int(input())
        # aのリスト完成
    for x in range(l,r+1):
        for i in range(1,n+1):
            if x%a[i-1]==0:
                if i%2==1:
                    cnt += 1
                break
            if i==n and n%2==0:
                cnt += 1
    print(cnt)
            
