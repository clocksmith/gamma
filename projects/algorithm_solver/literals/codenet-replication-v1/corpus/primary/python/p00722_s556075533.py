import math

def main():
    while True:
        a, d, n = map(int, input().split())
        if a == 0: break

        print(showprime(a, d, n))

    return

def showprime(a, d, n):
    i = 0
    while True:
        i += isprime(a)
        if i == n: return a
        a += d

def isprime(num):
    if num == 0 or num == 1: return 0
    sq_num = int(math.sqrt(num))

    for i in range(2, sq_num + 1):
        if num % i == 0: return 0

    return 1
main()

