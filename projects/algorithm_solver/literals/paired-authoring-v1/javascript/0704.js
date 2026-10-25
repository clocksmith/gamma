function lowerBound(values, target) {
  let left = 0;
  let right = values.length;
  while (left < right) {
    const middle = left + Math.floor((right - left) / 2);
    if (values[middle] < target) {
      left = middle + 1;
    } else {
      right = middle;
    }
  }
  return left;
}

class Solution {
  search(nums, target) {
    const index = lowerBound(nums, target);
    if (index === nums.length || nums[index] !== target) {
      return -1;
    }
    return index;
  }
}
