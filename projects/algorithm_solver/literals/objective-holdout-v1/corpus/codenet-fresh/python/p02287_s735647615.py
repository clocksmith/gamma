def parent(i):
    return(i // 2)

def left(i):
    return(i * 2)

def right(i):
    return(i * 2 + 1)

H = int(input())
A_list = list(map(int, input().split()))
A_list.insert(0, 0)
for i in range(1, H+1):
    print("node ", i, ": key = ", A_list[i], ", ", sep="", end="")
    if parent(i) >= 1:
        print("parent key = ", A_list[parent(i)], ", ", sep="", end="")
    if left(i) <= H:
        print("left key = ", A_list[left(i)], ", ", sep="", end="")
    if right(i) <= H:
        print("right key = ", A_list[right(i)], ", ", sep="", end="")
    print("")
