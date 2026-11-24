BASE = 4

while True:

    input_num = int(input())

    if input_num == -1:
        break

    result = ""

    while True:
        quotient, remainder = divmod(input_num, BASE)

        result = str(remainder) + result

        if input_num < BASE:
            break

        input_num = quotient

    print(result)

