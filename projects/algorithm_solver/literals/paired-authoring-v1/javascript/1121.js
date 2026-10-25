class Solution {
  canDivideIntoSubsequences(nums, k) {
    let maximum = 0;
    let runLength = 0;
    let previous = null;
    for (const value of nums) {
      if (value === previous) {
        runLength += 1;
      } else {
        runLength = 1;
      }
      maximum = Math.max(maximum, runLength);
      previous = value;
    }
    return maximum <= Math.floor(nums.length / k);
  }
}
