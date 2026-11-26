s=input()

c=False

for i in range(len(s)):
    if c==False and s[i]=="C":
        c=True
    elif c==True and s[i]=="F":
        print("Yes")
        exit()
print("No")