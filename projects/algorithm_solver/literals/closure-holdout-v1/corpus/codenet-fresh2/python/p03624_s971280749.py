S = input()

alpha = [chr(i) for i in range(97, 97+26)]

remain = list(set(alpha) - set(S))

if remain == []:
    print("None")
else:
    remain.sort()
    print(remain[0])
