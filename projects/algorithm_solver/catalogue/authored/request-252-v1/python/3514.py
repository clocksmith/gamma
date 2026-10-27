# Original candidate; contract and evidence: ../batch1/manifest.json
def solve(nums):
    width = 1 << max(nums).bit_length()
    values = [0] * width
    for number in nums:
        values[number] = 1

    def transform():
        step = 1
        while step < width:
            for start in range(0, width, 2 * step):
                for offset in range(step):
                    a, b = values[start + offset], values[start + step + offset]
                    values[start + offset] = a + b
                    values[start + step + offset] = a - b
            step *= 2

    transform()
    values[:] = [value ** 3 for value in values]
    transform()
    return sum(value > 0 for value in values)
