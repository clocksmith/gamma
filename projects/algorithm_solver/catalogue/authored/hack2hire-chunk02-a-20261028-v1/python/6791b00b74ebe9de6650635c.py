"""Hack2Hire 6791b00b74ebe9de6650635c (Generate Random NFT, v1); INFERRED spec, injected randomness; qualification unknown."""


def solve(traits, n, randoms):
    out, k = [], 0
    for _ in range(n):
        nft = []
        for _, values in traits:
            nft.append(values[randoms[k] % len(values)]); k += 1
        out.append(nft)
    return out


class Solution:
    def generateNFTs(self, traits, n, randoms):
        return solve(traits, n, randoms)
