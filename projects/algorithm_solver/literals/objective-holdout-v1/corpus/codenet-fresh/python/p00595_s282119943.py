import fileinput

for a, b in (map(int, line.split()) for line in fileinput.input()):
    if a > b:
        a, b = b, a
    while a:
        a, b = b % a, a
    print(b)