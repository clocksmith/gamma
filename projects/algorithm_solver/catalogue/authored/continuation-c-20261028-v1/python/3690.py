def solve(nums1, nums2):
    start, target = tuple(nums1), tuple(nums2)
    if start == target: return 0
    front, back = {start}, {target}
    own, other = {start: 0}, {target: 0}
    n = len(start)
    while front and back:
        if len(front) > len(back):
            front, back = back, front
            own, other = other, own
        following = set()
        for row in front:
            distance = own[row]+1
            for left in range(n):
                for right in range(left+1, n+1):
                    block = row[left:right]
                    rest = row[:left]+row[right:]
                    for position in range(len(rest)+1):
                        nxt = rest[:position]+block+rest[position:]
                        if nxt in own: continue
                        if nxt in other: return distance+other[nxt]
                        own[nxt] = distance
                        following.add(nxt)
        front = following
    return -1

class Solution:
    def minSplitMerge(self, nums1, nums2):
        return solve(nums1, nums2)
