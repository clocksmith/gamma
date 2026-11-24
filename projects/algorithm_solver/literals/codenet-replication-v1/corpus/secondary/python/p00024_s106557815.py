while True:
    try:
        v=float(input())
        t=v/9.8
        y=4.9*t**2
        N=0
        while y>5*(N-1):
            N +=1
        print(N)
    except:break
