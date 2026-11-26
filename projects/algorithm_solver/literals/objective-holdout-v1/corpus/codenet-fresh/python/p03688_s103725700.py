n = int(input())
a = list(map(int,input().split()))
b = list(a)
b.sort()
if b[n-1]-b[0] >=2:
    print("No")
else:
    b = sum(a)%n
    c = int((sum(a)-b)/n)
    if b == 0:
        if 2*c > n and n != c+1:
            print("No")
        else:
            print("Yes")
    else:
        if b == 1:
            print("No")
        else:
            if n - b/2 >= c+1 and n <= c+b:
                print("Yes")
            else:
                print("No")