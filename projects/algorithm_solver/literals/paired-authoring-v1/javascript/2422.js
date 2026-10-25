class Solution {
  minimumOperations(nums) {
    if (nums.length === 0) {
      return 0;
    }
    let left = 0;
    let right = nums.length - 1;
    let leftSum = nums[left];
    let rightSum = nums[right];
    let merges = 0;
    while (left < right) {
      if (leftSum === rightSum) {
        left += 1;
        right -= 1;
        if (left < right) {
          leftSum = nums[left];
          rightSum = nums[right];
        }
      } else if (leftSum < rightSum) {
        left += 1;
        leftSum += nums[left];
        merges += 1;
      } else {
        right -= 1;
        rightSum += nums[right];
        merges += 1;
      }
    }
    return merges;
  }
}
