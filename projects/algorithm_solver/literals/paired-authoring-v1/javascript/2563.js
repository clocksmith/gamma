function countBoundedPairs(values, limit, inclusive) {
  let left = 0;
  let right = values.length - 1;
  let count = 0;
  while (left < right) {
    const total = values[left] + values[right];
    if (total < limit || (inclusive && total === limit)) {
      count += right - left;
      left += 1;
    } else {
      right -= 1;
    }
  }
  return count;
}


class Solution {
  countFairPairs(nums, lower, upper) {
    const ordered = nums.slice().sort((first, second) => first - second);
    const atMostUpper = countBoundedPairs(ordered, upper, true);
    const belowLower = countBoundedPairs(ordered, lower, false);
    return atMostUpper - belowLower;
  }
}
