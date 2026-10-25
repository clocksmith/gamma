class Solution {
  arithmeticTriplets(nums, diff) {
    const seen = new Set();
    let count = 0;
    for (const value of nums) {
      if (seen.has(value - diff) && seen.has(value - 2 * diff)) {
        count += 1;
      }
      seen.add(value);
    }
    return count;
  }
}
