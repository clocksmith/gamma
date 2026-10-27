def solve(s):
    n = len(s)
    zeros = [i for i, c in enumerate(s) if c == '0'] + [n]
    first = 0
    answer = 0
    for left in range(n):
        if zeros[first] < left:
            first += 1
        answer += zeros[first] - left  # Substrings containing no zero.
        count = 1
        while count * count + count <= n - left and first + count < len(zeros):
            last_zero = zeros[first + count - 1]
            next_zero = zeros[first + count]
            # With count zeros, length must be at least count**2 + count.
            minimum_right = max(last_zero, left + count * count + count - 1)
            answer += max(0, next_zero - minimum_right)
            count += 1
    return answer
