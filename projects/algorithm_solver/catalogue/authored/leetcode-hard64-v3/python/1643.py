"""1643. Kth Smallest Instructions: binomial unranking with H before V; O((rows+columns)^2) time and space."""


def solve(destination: list[int], k: int) -> str:
    vertical, horizontal = destination
    total = vertical + horizontal
    choose = [[1]]
    for length in range(1, total + 1):
        row = [1] * (length + 1)
        for count in range(1, length):
            row[count] = choose[-1][count - 1] + choose[-1][count]
        choose.append(row)
    answer = []
    while vertical and horizontal:
        horizontal_first = choose[vertical + horizontal - 1][horizontal - 1]
        if k <= horizontal_first:
            answer.append('H')
            horizontal -= 1
        else:
            answer.append('V')
            vertical -= 1
            k -= horizontal_first
    return ''.join(answer) + 'H' * horizontal + 'V' * vertical


class Solution:
    def kthSmallestPath(self, destination: list[int], k: int) -> str:
        return solve(destination, k)
