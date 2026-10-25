class Solution {
  validSubarrays(nums) {
    const starts = [];
    let total = 0;
    for (const value of nums) {
      while (starts.length > 0 && starts[starts.length - 1] > value) {
        starts.pop();
      }
      starts.push(value);
      total += starts.length;
    }
    return total;
  }
}
