class Solution {
  findUnsortedSubarray(nums) {
    if (nums.length < 2) {
      return 0;
    }

    let left = nums.length;
    let right = -1;
    let largest = nums[0];
    for (let index = 1; index < nums.length; index += 1) {
      if (nums[index] < largest) {
        right = index;
      } else {
        largest = nums[index];
      }
    }
    let smallest = nums[nums.length - 1];
    for (let index = nums.length - 2; index >= 0; index -= 1) {
      if (nums[index] > smallest) {
        left = index;
      } else {
        smallest = nums[index];
      }
    }
    return right < left ? 0 : right - left + 1;
  }
}
