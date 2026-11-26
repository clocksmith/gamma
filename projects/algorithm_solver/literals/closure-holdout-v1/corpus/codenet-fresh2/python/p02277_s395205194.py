import sys
import itertools
sys.setrecursionlimit(1000000000)
from heapq import heapify,heappop,heappush,heappushpop
import math
import collections
import copy


def Partition(A,p,r):
    x = A[r][1]
    i = p - 1
    for j in range(p,r):
        if A[j][1] <= x:
            i = i + 1
            tmp = A[i]
            A[i] = A[j]
            A[j] = tmp
    tmp2 = A[i+1]
    A[i+1] = A[r]
    A[r] = tmp2
    return i + 1

def QuickSort(A,p,r):
    if p<r:
        q = Partition(A,p,r)
        QuickSort(A,p,q-1)
        QuickSort(A,q+1,r)

if __name__ == "__main__":
    n = int(input())
    card = []
    for i in range(n):
        key,val = input().split()
        card.append([key,int(val)])
    card2 = copy.copy(card)
    card2.sort(key= lambda x:x[1])
    QuickSort(card,0,n-1)
    if card2 == card:
        print("Stable")
    else:
        print("Not stable")
    for i in range(n):
        print(card[i][0],card[i][1])
