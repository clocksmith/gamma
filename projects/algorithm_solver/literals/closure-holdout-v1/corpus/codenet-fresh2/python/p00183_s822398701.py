def b_or_w(b_1, b_2, b_3):
    b, w = 'bbb', 'www'
    board = [b_1, b_2, b_3]
    for i in range(3):
        col = b_1[i] + b_2[i] + b_3[i]
        board.append(col)
    board.append(b_1[0] + b_2[1] + b_3[2])
    board.append(b_1[2] + b_2[1] + b_3[0])
    for bod in board:
        if bod == b:
            return 'b'
        elif bod == w:
            return 'w'
    else:
        return 'NA'

while True:
    b_1 = input()
    if b_1 == '0': break
    b_2, b_3 = input(), input()
    print(b_or_w(b_1, b_2, b_3))

