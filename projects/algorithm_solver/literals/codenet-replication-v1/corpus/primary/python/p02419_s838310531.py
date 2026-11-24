w = input()
counter = 0

while True:
        i = input()
        if i == 'END_OF_TEXT':
            break
        words = i.lower().split()
        counter += words.count(w)


print(counter)
