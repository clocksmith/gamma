class Solution {
  numberOfWays(startPos, endPos, k) {
    const distance = Math.abs(endPos - startPos);
    if (distance > k || (k - distance) % 2 !== 0) {
      return 0;
    }
    const chosen = (k - distance) / 2;
    const counts = Array(chosen + 1).fill(0);
    counts[0] = 1;
    const modulus = 1000000007;
    for (let steps = 1; steps <= k; steps += 1) {
      for (let index = Math.min(steps, chosen); index > 0; index -= 1) {
        counts[index] = (counts[index] + counts[index - 1]) % modulus;
      }
    }
    return counts[chosen];
  }
}
