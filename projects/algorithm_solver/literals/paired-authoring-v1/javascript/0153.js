class Solution {
  findMin(nums) {
    let left = 0;
    let right = nums.length - 1;
    // The minimum remains in the closed interval [left, right].
    while (left < right) {
      const middle = left + Math.floor((right - left) / 2);
      if (nums[middle] > nums[right]) {
        left = middle + 1;
      } else {
        right = middle;
      }
    }
    return nums[left];
  }
}
