# Original candidate; contract and evidence: ../batch1/manifest.json
def solve(s):
    ones = answer = 0
    for i, bit in enumerate(s):
        if bit == '1':
            ones += 1
        elif i > 0 and s[i - 1] == '1':
            answer += ones
    return answer
