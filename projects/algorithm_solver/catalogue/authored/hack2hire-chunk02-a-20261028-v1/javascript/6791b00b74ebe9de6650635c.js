"use strict";
// Hack2Hire 6791b00b74ebe9de6650635c (Generate Random NFT, v1); INFERRED spec, injected randomness; qualification unknown.
function solve(traits, n, randoms) {
  const out = [];
  let k = 0;
  for (let i = 0; i < n; i++) {
    const nft = [];
    for (const [, values] of traits) nft.push(values[randoms[k++] % values.length]);
    out.push(nft);
  }
  return out;
}
function generateNFTs(traits, n, randoms) { return solve(traits, n, randoms); }
module.exports = solve;
module.exports.generateNFTs = generateNFTs;
