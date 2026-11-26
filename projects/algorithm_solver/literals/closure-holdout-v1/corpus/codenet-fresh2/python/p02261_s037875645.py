# 安定なソート
import copy


def BubbleSort(C, N):
    for i in range(0, N):
        for j in range(N - 1, i, -1):
            if C[j].value < C[j - 1].value:
                C[j], C[j-1] = C[j-1], C[j]


def SelectionSort(C, N):
    for i in range(0, N):
        minj = i
        for j in range(i, N):
            if C[j].value < C[minj].value:
                minj = j
        C[i], C[minj] = C[minj], C[i]


class Card:
    value = 0
    x = ""

    def __init__(self, x):
        self.x = x
        self.value = int(x[1])


N = int(input())
C = list(map(lambda x: Card(x), input().split(" ")))

c1 = copy.copy(C)
c2 = copy.copy(C)

BubbleSort(c1, N)
SelectionSort(c2, N)
print(" ".join([x.x for x in c1]))
print("Stable")
print(" ".join([x.x for x in c2]))
isStable = True
for i in range(0, N):
    if c1[i] != c2[i]:
        isStable = False
        break
if isStable:
    print("Stable")
else:
    print("Not stable")

