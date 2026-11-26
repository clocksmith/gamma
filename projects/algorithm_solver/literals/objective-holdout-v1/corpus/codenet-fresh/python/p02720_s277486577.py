from collections import deque


def nth_ll(k):
    if k < 10:
        return k
    queue = deque([i for i in range(1, 10)])
    cnt = 9
    while True:
        n = queue.popleft()
        first_d = n % 10
        for i in range(-1, 2):
            if first_d + i < 0 or first_d + i > 9:
                continue
            queue.append(10 * n + first_d + i)
            cnt += 1
            if cnt == k:
                return queue.pop()

print(nth_ll(int(input())))
