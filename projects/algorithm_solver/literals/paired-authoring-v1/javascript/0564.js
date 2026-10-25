class Solution {
  nearestPalindromic(n) {
    const length = n.length;
    const value = BigInt(n);
    const prefix_length = Math.floor((length + 1) / 2);
    const prefix = BigInt(n.slice(0, prefix_length));
    const candidates = [10n ** BigInt(length - 1) - 1n, 10n ** BigInt(length) + 1n];
    for (const change of [-1n, 0n, 1n]) {
      const leading = String(prefix + change);
      if (leading.length !== prefix_length) {
        continue;
      }
      const reflected = length % 2 === 0 ? leading : leading.slice(0, -1);
      candidates.push(BigInt(leading + reflected.split("").reverse().join("")));
    }

    let best = null;
    let best_distance = 0n;
    for (const candidate of candidates) {
      if (candidate === value) {
        continue;
      }
      const difference = candidate - value;
      const distance = difference < 0n ? -difference : difference;
      if (best === null || distance < best_distance || (distance === best_distance && candidate < best)) {
        best = candidate;
        best_distance = distance;
      }
    }
    return String(best);
  }
}
