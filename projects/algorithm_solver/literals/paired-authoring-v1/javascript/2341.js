class Solution {
  numberOfPairs(nums) {
    const unmatched = new Set();
    let pairs = 0;
    for (const value of nums) {
      if (unmatched.has(value)) {
        unmatched.delete(value);
        pairs += 1;
      } else {
        unmatched.add(value);
      }
    }
    return [pairs, unmatched.size];
  }
}
