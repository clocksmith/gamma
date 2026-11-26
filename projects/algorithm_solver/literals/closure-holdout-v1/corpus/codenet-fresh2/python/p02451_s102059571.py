import bisect

def main():
    n = int(input())
    a = list(map(int,input().split()))
    m = int(input())
    for _ in range(m):
        b = int(input())
        index = bisect.bisect_left(a,b)
        if index<n and a[index]==b  :print (1)
        else                        :print (0)



if __name__ == '__main__':
    main()


