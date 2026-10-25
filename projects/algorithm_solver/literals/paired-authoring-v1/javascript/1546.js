class Solution {
  maxNonOverlapping(nums, target) {
    let prefixes = new Set([0]);
    let total = 0;
    let count = 0;
    for (const value of nums) {
      total += value;
      if (prefixes.has(total - target)) {
        count += 1;
        total = 0;
        prefixes = new Set([0]);
      } else {
        prefixes.add(total);
      }
    }
    return count;
  }
}
