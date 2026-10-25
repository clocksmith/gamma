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

function upperBound(values, target) {
  let left = 0;
  let right = values.length;
  while (left < right) {
    const middle = left + Math.floor((right - left) / 2);
    if (values[middle] <= target) {
      left = middle + 1;
    } else {
      right = middle;
    }
  }
  return left;
}

class Solution {
  searchRange(nums, target) {
    const first = lowerBound(nums, target);
    if (first === nums.length || nums[first] !== target) {
      return [-1, -1];
    }
    const last = upperBound(nums, target) - 1;
    return [first, last];
  }
}
