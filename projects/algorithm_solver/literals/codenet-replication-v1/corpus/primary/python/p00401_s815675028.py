n=int(input())
a=1
while(n>2**a):
    a+=1
if(n==2**a):
    print(2**a)
else:
    print(2**(a-1))
