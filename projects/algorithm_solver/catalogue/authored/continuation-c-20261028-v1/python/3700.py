def solve(n, l, r):
    modulus = 1000000007
    width = r-l+1
    size = width-1
    #Reflection swaps the up/down orientations. T maps either reflected state
    #to the next one; value zero has no incoming strict-up edge and is omitted.
    matrix = [[int(j+1 >= width-(i+1)) for j in range(size)] for i in range(size)]
    vector = [1]*size
    exponent = n-1
    def square(a):
        out = [[0]*size for _ in range(size)]
        for i in range(size):
            for k in range(size):
                factor = a[i][k]
                if factor:
                    for j in range(size): out[i][j] += factor*a[k][j]
            out[i] = [v % modulus for v in out[i]]
        return out
    while exponent:
        if exponent % 2:
            vector = [sum(matrix[i][j]*vector[j] for j in range(size)) % modulus for i in range(size)]
        exponent //= 2
        if exponent: matrix = square(matrix)
    return 2*sum(vector) % modulus

class Solution:
    def zigZagArrays(self, n, l, r):
        return solve(n, l, r)
