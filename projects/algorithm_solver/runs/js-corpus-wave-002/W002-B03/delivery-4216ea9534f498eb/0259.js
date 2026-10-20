function threeSumSmaller(nums, target) {
  const sorted = [...nums].sort((a, b) => a - b);
  let count = 0;
  for (let i = 0; i < sorted.length - 2; i++) {
    let left = i + 1, right = sorted.length - 1;
    while (left < right) {
      if (sorted[i] + sorted[left] + sorted[right] < target) { count += right - left; left++; }
      else right--;
    }
  }
  return count;
}
