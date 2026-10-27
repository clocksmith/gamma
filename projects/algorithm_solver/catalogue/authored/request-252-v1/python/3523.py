# Original candidate; contract and evidence: ../batch1/manifest.json
def solve(nums):
    maximum = 0
    answer = 0
    for number in nums:
        if number >= maximum:
            maximum = number
            answer += 1
    return answer
