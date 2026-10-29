"use strict";
// Hack2Hire 6791b5ff74ebe9de6650635e (Generate Random NFT, v3 unique); INFERRED spec, injected randomness; qualification unknown.
// All quantities stay below 2^53 under the inferred domain (T <= 50^8, randoms <= 10^15), so Number arithmetic is exact.
function solve(traits, n, randoms) {
  const sizes = traits.map(t => t[1].length);
  let total = 1;
  for (const s of sizes) total *= s;
  if (n > total) return [];
  const moved = new Map(), out = [];
  for (let i = 0; i < n; i++) {
    const j = i + randoms[i] % (total - i);
    const pick = moved.has(j) ? moved.get(j) : j;
    moved.set(j, moved.has(i) ? moved.get(i) : i);
    let index = pick;
    const nft = new Array(traits.length);
    for (let t = traits.length - 1; t >= 0; t--) { const d = index % sizes[t]; nft[t] = traits[t][1][d]; index = (index - d) / sizes[t]; }
    out.push(nft);
  }
  return out;
}
function generateUniqueNFTs(traits, n, randoms) { return solve(traits, n, randoms); }
module.exports = solve;
module.exports.generateUniqueNFTs = generateUniqueNFTs;
