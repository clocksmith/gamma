class Solution {
  longestConsecutive(nums) {
    const values = new Set(nums);
    let longest = 0;
    for (const value of values) {
      if (values.has(value - 1)) {
        continue;
      }
      let current = value;
      let length = 1;
      while (values.has(current + 1)) {
        current += 1;
        length += 1;
      }
      longest = Math.max(longest, length);
    }
    return longest;
  }
}
