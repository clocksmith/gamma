import sys
sys.setrecursionlimit(100000)

def intinput(): return map(int,input().split())

def x(s):
    try:
        s.index("##")
    except:
        return True
    else:
        return False

n,a,b,c,d=intinput()
s=input()
if c<d:
    if x(s[a-1:d]):
        print("Yes")
    else:
        print("No")
else:
    try:
        s[b-2:d+1].index("...")
    except:
        print("No")
    else:
        if x(s[a - 1:c]):
            print("Yes")
        else:
            print("No")