import re

SNAKE_A = re.compile(r">'(=+)#\1~")
SNAKE_B = re.compile(r">\^(Q=)+~~")


def answer(regex, string, output):
    result = regex.fullmatch(string)

    if result is not None:
        print(output)
    else:
        print("NA")


for _ in range(int(input())):

    snake = input()

    if snake[1] == "'":
        answer(SNAKE_A, snake, "A")
    else:
        answer(SNAKE_B, snake, "B")

