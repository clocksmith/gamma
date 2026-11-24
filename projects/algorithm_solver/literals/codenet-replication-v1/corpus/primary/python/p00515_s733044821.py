list=[]
a=0
for i in range (5):
    n=int(input())
    if n<=40:
        n=40
    list.append(n)
    a+=list[i]
print(a//5)

