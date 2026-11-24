MAX_X = 2000
MAX_Y = 2000
s = [ [0 for i in range(MAX_X)] for j in range(MAX_Y) ]
for _ in range (2) :
    x,y,w,h = map(int,input().split())
    for i in range(x,x+w) :
        for j in range(y,y+h) :
            s[i][j] += 1
c = 0
for i in range(0,MAX_X) :
    for j in range(0,MAX_Y) :
        if s[i][j] == 1 : c += 1
print(c)

