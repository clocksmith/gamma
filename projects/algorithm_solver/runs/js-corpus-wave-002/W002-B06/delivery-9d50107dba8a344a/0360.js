function sortTransformedArray(nums, a, b, c) {
  function transform(value) {
    return (a * value + b) * value + c;
  }

  const result = new Array(nums.length);
  let left = 0;
  let right = nums.length - 1;
  let output = a > 0 ? nums.length - 1 : 0;

  while (left <= right) {
    const leftValue = transform(nums[left]);
    const rightValue = transform(nums[right]);
    if (a > 0) {
      if (leftValue > rightValue) {
        result[output--] = leftValue;
        left++;
      } else {
        result[output--] = rightValue;
        right--;
      }
    } else if (leftValue < rightValue) {
      result[output++] = leftValue;
      left++;
    } else {
      result[output++] = rightValue;
      right--;
    }
  }
  return result;
}
