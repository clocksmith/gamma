class Solution {
  numRollsToTarget(n, k, target) {
    const modulus = 1000000007;
    let previous = Array(target + 1).fill(0);
    previous[0] = 1;
    for (let die = 0; die < n; die += 1) {
      const current = Array(target + 1).fill(0);
      for (let total = 1; total <= target; total += 1) {
        let ways = 0;
        for (let face = 1; face <= Math.min(k, total); face += 1) {
          ways = (ways + previous[total - face]) % modulus;
        }
        current[total] = ways;
      }
      previous = current;
    }
    return previous[target];
  }
}
