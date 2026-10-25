class Solution {
  findLHS(nums) {
    const counts = new Map();
    for (const value of nums) {
      counts.set(value, (counts.get(value) || 0) + 1);
    }
    let longest = 0;
    for (const [value, count] of counts) {
      if (counts.has(value + 1)) {
        longest = Math.max(longest, count + counts.get(value + 1));
      }
    }
    return longest;
  }
}
