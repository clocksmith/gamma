"""Original development candidate for frontend 3720; qualification pending."""

def solve(s, target):
    counts = [0] * 26
    for char in s:
        counts[ord(char) - 97] += 1
    matched = 0
    while matched < len(target) and counts[ord(target[matched]) - 97]:
        counts[ord(target[matched]) - 97] -= 1
        matched += 1
    for pivot in range(matched, -1, -1):
        if pivot < matched:
            counts[ord(target[pivot]) - 97] += 1
        if pivot == len(target):
            continue
        for index in range(ord(target[pivot]) - 96, 26):
            if counts[index]:
                counts[index] -= 1
                return target[:pivot] + chr(97 + index) + ''.join(chr(97 + j) * count for j, count in enumerate(counts))
    return ''


class Solution:
    def lexGreaterPermutation(self, s, target):
        return solve(s, target)
