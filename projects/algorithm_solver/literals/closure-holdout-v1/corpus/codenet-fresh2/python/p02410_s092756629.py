if __name__ == '__main__':
    n, m = [int(i) for i in input().split()]
    A = [[int(i) for i in input().split()] for j in range(n)]
    b = [int(input()) for i in range(m)]
    c = [sum(map(lambda x,y: x*y, A[i], b)) for i in range(n)]
    print('\n'.join([str(i) for i in c]))