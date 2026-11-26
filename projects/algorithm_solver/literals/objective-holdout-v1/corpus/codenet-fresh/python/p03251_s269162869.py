n, m, x, y = map(int, input().split())
xl = list(map(int, input().split()))
yl = list(map(int, input().split()))
xl.sort()
yl.sort()
ans = False
if x < y and x < xl[n - 1] < yl[0] < y:
    ans = True
    
print("No War" if ans else "War")