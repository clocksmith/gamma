def left_empty(bench):
    return bench.index('#') 

def a_sit(bench):
    bench[left_empty(bench)] = 'A'
def right_empty(bench):
    for i in reversed(range(len(bench))):
        if bench[i] == '#':
            yield i

def a_next(bench, i):
    if i + 1 < len(bench) and bench[i + 1] == 'A':
        return True
    if 0 <= i - 1 and bench[i - 1] == 'A':
        return True
    return False
            
def b_sit(bench):
    for i in right_empty(bench):
        if not a_next(bench,i):
            bench[i] = 'B'
            return
    bench[left_empty(bench)] = 'B'
def no_people(bench):
    for bi in bench:
        if bi != '#':
            return False
    return True

def not_empty(bench):
    for i in range(len(bench)):
        if bench[i] != '#':
            yield i

def c_sit(bench):
    if no_people(bench):
        bench[len(bench) // 2] = 'C'
        return
    for i in not_empty(bench):
        if i + 1 < len(bench) and bench[i + 1] == '#':
            bench[i + 1] = 'C'
            return
        if 0 <= i - 1 and bench[i - 1] == '#':
            bench[i - 1] = 'C'
            return
def d_sit(bench):
    if no_people(bench):
        bench[0] = 'D'
        return
    tmp = bench[:]
    
    dist = float('inf')
    for i in range(len(tmp)):
        if tmp[i] == '#':
            dist += 1
        else:
            dist = 0
        tmp[i] = dist
    dist = float('inf')
    for i in reversed(range(len(tmp))):
        if tmp[i] != 0:
            dist += 1
        else:
            dist = 0
        tmp[i] = min(tmp[i], dist)
    bench[tmp.index(max(tmp))] = 'D'

import sys
f = sys.stdin


sit = {'A':a_sit,'B':b_sit,'C':c_sit,'D':d_sit}
while True:
    m, n = map(int, f.readline().split())
    if n == 0:
        break
    bench = ['#'] * m
    for i in range(n):
        sit[f.readline().strip()](bench)
    print(''.join(bench))