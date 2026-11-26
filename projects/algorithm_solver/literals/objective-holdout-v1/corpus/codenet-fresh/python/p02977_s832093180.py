import sys
readline = sys.stdin.readline       
N = int(readline())

ans = 'Yes' if -N&N != N else 'No'
print(ans)
if ans == 'Yes':
    Edge = []
    
    for i in range(2, N-(N%2 == 0)+1):
        Edge.append((1, i))
        if not i&1:
            Edge.append((i, N+i+1))
            Edge.append((i+1, N+i))
    Edge.append((N+1, N+3))
    if not N&1:
        Edge.append(((-N&N)+1, N))
        Edge.append((N^(-N&N), N+N))
    print('\n'.join([' '.join(map(str, e)) for e in Edge]))
