"""Hack2Hire 6a19fed3c81f779dc6a2370d (Assign Random Ads) over an INFERRED spec; qualification unknown."""


def solve(browserPositions, candidateAds, userAdState, randomIndices):
    eligible = [ad['adId'] for ad in candidateAds if userAdState.get(ad['adId'], 0) < ad['maxDisplay']]
    size = len(eligible)
    tree = [0] * (size + 1)
    for i in range(1, size + 1):
        tree[i] += 1
        parent = i + (i & -i)
        if parent <= size:
            tree[parent] += tree[i]
    top = 1
    while top * 2 <= size:
        top *= 2
    remaining, result = size, []
    for i in range(len(browserPositions)):
        if remaining == 0:
            result.append(None)
            continue
        rank = randomIndices[i] % remaining + 1  # 1-based order statistic among still-eligible ads
        position, step = 0, top
        while step:
            if position + step <= size and tree[position + step] < rank:
                position += step
                rank -= tree[position]
            step //= 2
        chosen = position + 1
        result.append(eligible[chosen - 1])
        while chosen <= size:
            tree[chosen] -= 1
            chosen += chosen & -chosen
        remaining -= 1
    return result


class Solution:
    def assignAds(self, browserPositions, candidateAds, userAdState, randomIndices):
        return solve(browserPositions, candidateAds, userAdState, randomIndices)
