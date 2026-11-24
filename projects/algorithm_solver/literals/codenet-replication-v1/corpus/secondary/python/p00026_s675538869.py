import sys

lines = []
for line in sys.stdin:
    lines.append(line.strip().split(','))

field = [[0 for i in range(10)] for j in range(10)]

def drop(x, y, z):
    if z==1:
        for i in range(-1,2):
            for j in range(-1,2):
                if abs(i)+abs(j)<2 and 0<=y+j<=9 and 0<=x+i<=9:
                    field[y+j][x+i] += 1
    elif z==2:
        for i in range(-1,2):
            for j in range(-1,2):
                if 0<=y+j<=9 and 0<=x+i<=9:
                    field[y+j][x+i] += 1
    else:
        for i in range(-2,3):
            for j in range(-2,3):
                if abs(i)+abs(j)<3 and 0<=y+j<=9 and 0<=x+i<=9:
                    field[y+j][x+i] += 1



for line in lines:
    x,y,z = map(int, line)
    drop(x,y,z)

n = 0
m = 0
for f in field:
    for e in f:
        if e > m:
            m = e
        if e==0:
            n+=1

print(n)
print(m)

