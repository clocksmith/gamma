# coding: utf-8
# Your code here!
a=[]
try:
    while True:
        a.append(int(input()))
except EOFError:
    pass
b=[0]*101

for i in a:
    b[i]+=1
c=max(b)

for i in range(100):
    if b[i]==c:
        print(i)
