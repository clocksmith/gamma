from collections import deque

def testcase_ends():
    n = int(input())
    if n == 0:
        return 1

    sub = [input().split() for i in range(n)]
    gamma = input()
    delta = input()

    q = deque()
    q.append((gamma, 0))
    res = 10000
    while q:
        s, i = q.popleft()
        for alpha, beta in sub:
            if alpha not in s: continue

            t = s.replace(alpha, beta)
            if t == delta:
                res = min(res, i+1)
                continue
            elif len(t) >= len(delta):
                continue

            q.append((t, i+1))

    if res == 10000: res = -1
    print(res)
    return 0

def main():
    while not testcase_ends():
        pass

if __name__ == '__main__':
    main()

