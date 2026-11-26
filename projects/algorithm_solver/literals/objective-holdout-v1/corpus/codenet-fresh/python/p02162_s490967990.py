t1, t2, r1, r2 = map(int, input().split())
if r1 != -1 and r2 != -1 :
    if r1 > r2 :
        print("Alice")
    elif r1 < r2 :
        print("Bob")
    else :
        print("Draw")
else :
    if t1 < t2 :
        print("Alice")
    elif t1 > t2 :
        print("Bob")
    else :
        print("Draw")
