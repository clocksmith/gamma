function maxNumber(nums1, nums2, k) {
  function bestSubsequence(numbers, size) {
    const stack = [];
    let removals = numbers.length - size;
    for (const digit of numbers) {
      while (removals > 0 && stack.length > 0 && stack[stack.length - 1] < digit) {
        stack.pop();
        removals--;
      }
      stack.push(digit);
    }
    return stack.slice(0, size);
  }

  function suffixAtLeast(left, leftIndex, right, rightIndex) {
    while (leftIndex < left.length && rightIndex < right.length &&
      left[leftIndex] === right[rightIndex]) {
      leftIndex++;
      rightIndex++;
    }
    if (rightIndex === right.length) return true;
    if (leftIndex === left.length) return false;
    return left[leftIndex] > right[rightIndex];
  }

  function merge(left, right) {
    const combined = [];
    let leftIndex = 0;
    let rightIndex = 0;
    while (leftIndex < left.length || rightIndex < right.length) {
      if (suffixAtLeast(left, leftIndex, right, rightIndex)) {
        combined.push(left[leftIndex++]);
      } else {
        combined.push(right[rightIndex++]);
      }
    }
    return combined;
  }

  let best = [];
  const minLeft = Math.max(0, k - nums2.length);
  const maxLeft = Math.min(k, nums1.length);
  for (let leftSize = minLeft; leftSize <= maxLeft; leftSize++) {
    const left = bestSubsequence(nums1, leftSize);
    const right = bestSubsequence(nums2, k - leftSize);
    const candidate = merge(left, right);
    if (best.length === 0 || suffixAtLeast(candidate, 0, best, 0)) best = candidate;
  }
  return best;
}
