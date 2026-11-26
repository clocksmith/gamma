while True:
    a,b = map(int,input().split())
    if a == b == 0:break
    else:
        for t in range(a):
            for y in range(b):
                if (t+y) % 2 == 0:
                    print("#", end="")
                else:
                    print(".", end="")
            print()
        print()
        
