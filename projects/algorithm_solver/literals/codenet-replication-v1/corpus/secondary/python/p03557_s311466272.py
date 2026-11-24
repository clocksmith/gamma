from bisect import bisect_left,bisect_right
def main():
    N = int(input())
    A = sorted(list(map(int,input().split())))
    B = sorted(list(map(int,input().split())))
    C = sorted(list(map(int,input().split())))
    ans = 0
    for b in B:
        a = bisect_left(A,b)
        c = bisect_right(C,b)
        ans += a*(N-c)
    print(ans)

if __name__ == "__main__":
    main()