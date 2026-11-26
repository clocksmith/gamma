import re
S=0
while True:
    try:
        x=input()
        R=re.compile("\d+")
        m=R.findall(x)
        M=[int(s) for s in m]
        S+=sum(M)
    except EOFError:
        break
print(S)
