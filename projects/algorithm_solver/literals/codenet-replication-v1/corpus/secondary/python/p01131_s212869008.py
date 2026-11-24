chars = (None, '.,!? ', 'abc', 'def', 'ghi', 'jkl', 'mno', 'pqrs', 'tuv', 'wxyz')
n = int(input())

while n:
    n -= 1
    s = input()
    number, counter = 0, 0
    for c in s:
        if c == '0':
            if number:
                charset = chars[number]
                print(charset[(counter - 1) % len(charset)], end='')
                number, counter = 0, 0
        elif counter:
            counter += 1
        else:
            number = int(c)
            counter = 1
    print()