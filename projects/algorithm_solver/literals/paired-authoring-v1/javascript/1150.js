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
  isMajorityElement(nums, target) {
    const count = upperBound(nums, target) - lowerBound(nums, target);
    return 2 * count > nums.length;
  }
}
