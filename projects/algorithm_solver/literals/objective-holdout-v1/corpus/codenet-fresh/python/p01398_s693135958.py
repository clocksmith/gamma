while 1:
    n=int(input())
    if n==0:break
    s=list(input())
    c=[list(map(int,input().split())) for _ in range(n)]
    for i,j in c[::-1]:
        d,i,j=j-i,i-1,j-1
        s[i],s[j]=chr((ord(s[j])-97+d)%26+97),chr((ord(s[i])-97+d)%26+97)
    print("".join(s))