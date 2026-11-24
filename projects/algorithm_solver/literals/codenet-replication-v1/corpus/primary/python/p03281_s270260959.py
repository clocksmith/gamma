N = int(input())

eight_number = 0

for i in range(1, N + 1, 2):

    count = 0

    for j in range(1, i + 1):
        if i % j == 0:
            count += 1

    if count == 8:
        eight_number += 1

print(eight_number)
