def prime(N):
    first=[True for i in range(N+1)]
    first[0],first[1]=False,False
    for i in range(2,int((N+1)**0.5)):
        if not first[i]:continue
        for j in range(i*2,N+1,i):first[j]=False
    return [i for i in range(N+1) if first[i]]

prime_number=prime(10000)
while 1:
    n=int(input())
    if n==0:break
    box=0
    for i,j in enumerate(prime_number):
        if j>n:break
        if prime_number[i]-prime_number[i-1]==2:
            box=max(box,prime_number[i])
    print(box-2,box)
