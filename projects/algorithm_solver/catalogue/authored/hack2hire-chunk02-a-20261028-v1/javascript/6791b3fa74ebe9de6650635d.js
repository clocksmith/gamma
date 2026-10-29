"use strict";
// Hack2Hire 6791b3fa74ebe9de6650635d (Generate Random NFT, v2 weighted); INFERRED spec, injected randomness; qualification unknown.
function solve(traits, n, randoms) {
  const prepared = traits.map(([, values]) => {
    const prefix = []; let acc = 0;
    for (const [, weight] of values) { acc += weight; prefix.push(acc); }
    return [values.map(v => v[0]), prefix, acc];
  });
  const out = [];
  let k = 0;
  for (let i = 0; i < n; i++) {
    const nft = [];
    for (const [names, prefix, total] of prepared) {
      const x = randoms[k++] % total;
      let lo = 0, hi = prefix.length - 1;  // first index with prefix > x
      while (lo < hi) { const mid = (lo + hi) >> 1; if (prefix[mid] > x) hi = mid; else lo = mid + 1; }
      nft.push(names[lo]);
    }
    out.push(nft);
  }
  return out;
}
function generateWeightedNFTs(traits, n, randoms) { return solve(traits, n, randoms); }
module.exports = solve;
module.exports.generateWeightedNFTs = generateWeightedNFTs;
