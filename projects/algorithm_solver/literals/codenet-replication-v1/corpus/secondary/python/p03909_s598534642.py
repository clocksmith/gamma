h,w=map(int,input().split())
a=[[i for i in input().split()] for j in range(h)]
p=[chr(i) for i in range(65,91)]
for r in range(h):
    for c in range(w):
        if a[r][c]=="snuke":
            print(p[c]+str(r+1))
            break