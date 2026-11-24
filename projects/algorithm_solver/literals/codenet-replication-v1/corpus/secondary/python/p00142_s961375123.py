import itertools
def func(n):
  rest = {i ** 2 % n for i in range(1, n)}

  count = [0] * n
  for x, y in itertools.combinations(rest, 2):
    count[x - y] += 2

  for i in range(n // 2):
    print(count[i + 1] + count[n - i - 1])


def main():
  while True:
    n = int(input())
    if n == 0:
      break
    func(n)

main()
