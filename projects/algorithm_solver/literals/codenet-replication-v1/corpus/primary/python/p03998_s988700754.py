sa=input()
sb=input()
sc=input()
x="a"
while True:
    if x=="a":
        if len(sa)==0:
            print("A")
            break
        x=sa[0]
        sa=sa[1:]
    elif x=="b":
        if len(sb)==0:
            print("B")
            break
        x=sb[0]
        sb=sb[1:]
    elif x=="c":
        if len(sc)==0:
            print("C")
            break
        x=sc[0]
        sc=sc[1:] 