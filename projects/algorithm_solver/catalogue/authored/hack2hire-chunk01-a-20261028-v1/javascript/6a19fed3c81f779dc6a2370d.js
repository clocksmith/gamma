"use strict";
// Hack2Hire 6a19fed3c81f779dc6a2370d (Assign Random Ads) over an INFERRED spec; qualification unknown.
function solve(browserPositions, candidateAds, userAdState, randomIndices) {
  const seenCount = (id) => (Object.prototype.hasOwnProperty.call(userAdState, id) ? userAdState[id] : 0);
  const eligible = candidateAds.filter((ad) => seenCount(ad.adId) < ad.maxDisplay).map((ad) => ad.adId);
  const size = eligible.length, tree = new Array(size + 1).fill(0);
  for (let i = 1; i <= size; i++) {
    tree[i] += 1;
    const parent = i + (i & -i);
    if (parent <= size) tree[parent] += tree[i];
  }
  let top = 1;
  while (top * 2 <= size) top *= 2;
  let remaining = size;
  const result = [];
  for (let i = 0; i < browserPositions.length; i++) {
    if (remaining === 0) { result.push(null); continue; }
    let rank = randomIndices[i] % remaining + 1, position = 0;
    for (let step = top; step > 0; step = Math.floor(step / 2)) {
      if (position + step <= size && tree[position + step] < rank) { position += step; rank -= tree[position]; }
    }
    let chosen = position + 1;
    result.push(eligible[chosen - 1]);
    for (; chosen <= size; chosen += chosen & -chosen) tree[chosen] -= 1;
    remaining -= 1;
  }
  return result;
}
function assignAds(browserPositions, candidateAds, userAdState, randomIndices) { return solve(browserPositions, candidateAds, userAdState, randomIndices); }
module.exports = solve;
module.exports.assignAds = assignAds;
