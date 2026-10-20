function isMonotonicSequence(values) {
  let nondecreasing = true;
  let nonincreasing = true;
  for (let valueIndex = 1; valueIndex < values.length; valueIndex += 1) {
    if (values[valueIndex - 1] > values[valueIndex]) {
      nondecreasing = false;
    }
    if (values[valueIndex - 1] < values[valueIndex]) {
      nonincreasing = false;
    }
  }
  return nondecreasing || nonincreasing;
}
class Solution {
  isMonotonic(nums) {
    return isMonotonicSequence(nums);
  }
}
