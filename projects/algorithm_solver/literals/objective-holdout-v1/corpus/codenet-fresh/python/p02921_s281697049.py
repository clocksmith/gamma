s=str(input())
t=str(input())
count=0
for i in range(3):
    if s[i]==t[i]:
        count+=1
print(count)