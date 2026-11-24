A,B,C,X,Y = map(int,input().split())
if A+B <= C*2:
    print(A*X+B*Y)
    exit()
if (X>Y and A>=C*2) or (Y>X and B>=C*2):
    print(C*2*max(X,Y))
    exit()
price = min(X,Y)*C*2
if X >= Y:
    print(price+(X-Y)*A)
else:
    print(price+(Y-X)*B)