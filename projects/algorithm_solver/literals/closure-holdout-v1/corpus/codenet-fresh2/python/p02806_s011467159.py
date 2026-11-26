n=int(input())
st=[]
for i in range(n):
    s,t=input().split()
    t=int(t)
    st.append([s,t])
x=input()
j=0
for i in range(n):
    if st[i][0]==x:
        j=i
        break
ans=0
for i in range(j+1,n):
    ans+=st[i][1]
print(ans)
