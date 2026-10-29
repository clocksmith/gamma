"""Hack2Hire 6791b3fa74ebe9de6650635d (Generate Random NFT, v2 weighted); INFERRED spec, injected randomness; qualification unknown."""
from bisect import bisect_right


def solve(traits, n, randoms):
    prepared = []
    for _, values in traits:
        prefix, acc = [], 0
        for _, weight in values:
            acc += weight; prefix.append(acc)
        prepared.append(([v for v, _ in values], prefix, acc))
    out, k = [], 0
    for _ in range(n):
        nft = []
        for names, prefix, total in prepared:
            nft.append(names[bisect_right(prefix, randoms[k] % total)]); k += 1
        out.append(nft)
    return out


class Solution:
    def generateWeightedNFTs(self, traits, n, randoms):
        return solve(traits, n, randoms)
