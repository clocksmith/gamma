while 1:
    try:
        t500, t1000 = map(float, input().split())
    except EOFError:
        break

    if t500 < 35.5 and t1000 < 71:
        print("AAA")
    elif t500 < 37.5 and t1000 < 77:
        print("AA")
    elif t500 < 40 and t1000 < 83:
        print("A")
    elif t500 < 43 and t1000 < 89:
        print("B")
    elif t500 < 50 and t1000 < 105:
        print("C")
    elif t500 < 55 and t1000 < 116:
        print("D")
    elif t500 < 70 and t1000 < 148:
        print("E")
    else:
        print("NA")

