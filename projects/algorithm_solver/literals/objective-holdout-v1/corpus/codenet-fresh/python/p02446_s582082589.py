n=int(input())
A=list(map(int,input().split()))
A=sorted(list(set(A)))

print(' '.join(map(str,A)))

