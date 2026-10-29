"""Hack2Hire 6a18ebdbc81f779dc6a23112 (Count and Flip Binary Operations) over an INFERRED spec; qualification unknown."""


def solve(binaryString, requests):
    prefix = [0] * (len(binaryString) + 1)
    for i, ch in enumerate(binaryString):
        prefix[i + 1] = prefix[i] + (ch == '1')
    flipped, result = False, []
    for request in requests:
        if request == 'flip':
            flipped = not flipped
        else:
            index = int(request[6:])
            ones = prefix[index + 1]
            result.append(index + 1 - ones if flipped else ones)
    return result


class Solution:
    def processRequests(self, binaryString, requests):
        return solve(binaryString, requests)
