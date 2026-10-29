// 354 — Russian Doll Envelopes. Original implementation; authored candidate, not independently qualified.
function solve(envelopes) {
  const sorted = envelopes.map(p => p.slice()).sort((a,b) => a[0]-b[0] || b[1]-a[1]), tails = [];
  for (const [,height] of sorted) {
    let lo = 0, hi = tails.length;
    while (lo < hi) { const mid = Math.floor((lo+hi)/2); if (tails[mid] < height) lo = mid+1; else hi = mid; }
    tails[lo] = height;
  }
  return tails.length;
}

module.exports = { solve, maxEnvelopes: solve };
