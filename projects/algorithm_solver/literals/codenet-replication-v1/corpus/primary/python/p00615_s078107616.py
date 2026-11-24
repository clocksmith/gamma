if __name__ == '__main__':
    while True:
        L, R = list(map(int, input().strip().split()))
        if L == 0 and R == 0:
            break
            
        arr = set([ 0 ])
        if L > 0:
            arr.update( list(map(int, input().strip().split(' '))) )
        if R > 0:
            arr.update( list(map(int, input().strip().split(' '))) )
        arr = sorted(list(arr))

        maxi = -9999999999
        for i in range(len(arr) - 1):
            maxi = max(maxi, arr[i + 1] - arr[i])

        print(maxi)
