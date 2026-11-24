num = int(input())
for _ in range(num):
    P = 0
    B = [0] * 3
    O = 0
    while True:
        s = input()
        if s == "OUT":
            O += 1
            if O > 2:
                break
        elif s == "HIT":
            P += B[2]
            B[2] = B[1]
            B[1] = B[0]
            B[0] = 1
        elif s == "HOMERUN":
            P += sum(B)
            P += 1
            B = [0] * 3
        else:
            pass

    if O > 2:
        print(P)
        continue
   
