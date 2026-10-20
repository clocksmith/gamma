function countSmaller(nums) {
  const length = nums.length;
  const indices = Array.from({ length }, (_, index) => index);
  const buffer = new Array(length);
  const result = new Array(length).fill(0);

  function mergeSort(start, end) {
    if (end - start <= 1) return;
    const middle = start + Math.floor((end - start) / 2);
    mergeSort(start, middle);
    mergeSort(middle, end);

    let left = start;
    let right = middle;
    let output = start;
    while (left < middle && right < end) {
      if (nums[indices[right]] < nums[indices[left]]) {
        buffer[output++] = indices[right++];
      } else {
        result[indices[left]] += right - middle;
        buffer[output++] = indices[left++];
      }
    }
    while (left < middle) {
      result[indices[left]] += right - middle;
      buffer[output++] = indices[left++];
    }
    while (right < end) buffer[output++] = indices[right++];
    for (let index = start; index < end; index++) indices[index] = buffer[index];
  }

  mergeSort(0, length);
  return result;
}
