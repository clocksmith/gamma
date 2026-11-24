def play(line, N):
    C = [0] * N
    B = 0

    for i in range(len(line)):
        p = i%N
        if line[i] == 'M':
            C[p] += 1
        elif line[i] == 'S':
            C[p] += 1
            B += C[p]
            C[p] = 0
        elif line[i] == 'L':
            C[p] += B + 1
            B = 0

    C.sort();

    for c in C: print(c, end=" ")
    print(B)

while True:
    N = int(input())
    if N == 0: break
    line = input()
    play(line, N)
             
