# coding: utf-8
# Here your code !


def latte():
    return int(input())

while True:
    x=y=0
    n=latte()
    if n==0 :break
    for i in range(n):
        a,b=map(int,input().strip().split())
        if a>b:
            x+=a+b
        elif b>a:
            y+=a+b
        else :
            x+=a
            y+=b
    
    print(x,y)
    
    