class Solution {
  twoSumLessThanK(nums, k) {
    nums.sort((left, right) => left - right);
    let left = 0;
    let right = nums.length - 1;
    let best = -1;
    while (left < right) {
      const total = nums[left] + nums[right];
      if (total < k) {
        best = Math.max(best, total);
        left += 1;
      } else {
        right -= 1;
      }
    }
    return best;
  }
}
