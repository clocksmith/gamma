class Solution {
  largestPerimeter(nums) {
    const ordered = nums.slice().sort((left, right) => left - right);
    for (let index = ordered.length - 1; index >= 2; index -= 1) {
      if (ordered[index - 2] + ordered[index - 1] > ordered[index]) {
        return ordered[index - 2] + ordered[index - 1] + ordered[index];
      }
    }
    return 0;
  }
}
