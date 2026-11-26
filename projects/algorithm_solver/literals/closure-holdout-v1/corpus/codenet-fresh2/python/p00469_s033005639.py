while True:
    n=int(input())
    k=int(input())
    if n==0:
        break
    c=[input() for _ in [0]*n]
    
    s=set()
    
    from itertools import permutations
    
    cnt=0
    for i in permutations(range(n),k):
        s.add(int("".join([c[j] for j in i])))
    print(len(s))
