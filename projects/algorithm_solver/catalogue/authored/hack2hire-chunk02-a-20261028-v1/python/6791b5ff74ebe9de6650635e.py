"""Hack2Hire 6791b5ff74ebe9de6650635e (Generate Random NFT, v3 unique); INFERRED spec, injected randomness; qualification unknown."""


def solve(traits, n, randoms):
    sizes = [len(values) for _, values in traits]
    total = 1
    for size in sizes: total *= size
    if n > total: return []
    moved, out = {}, []
    for i in range(n):
        j = i + randoms[i] % (total - i)
        pick = moved.get(j, j)
        moved[j] = moved.get(i, i)
        index, nft = pick, [None] * len(traits)
        for t in range(len(traits) - 1, -1, -1):
            index, digit = divmod(index, sizes[t])
            nft[t] = traits[t][1][digit]
        out.append(nft)
    return out


class Solution:
    def generateUniqueNFTs(self, traits, n, randoms):
        return solve(traits, n, randoms)
