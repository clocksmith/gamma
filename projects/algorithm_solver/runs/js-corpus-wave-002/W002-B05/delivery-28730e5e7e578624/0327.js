function countRangeSum(nums, lower, upper) {
  const prefixes = new Array(nums.length + 1).fill(0);
  for (let index = 0; index < nums.length; index++) {
    prefixes[index + 1] = prefixes[index] + nums[index];
  }
  const buffer = new Array(prefixes.length);

  function countAndMerge(start, end) {
    if (end - start <= 1) return 0;
    const middle = start + Math.floor((end - start) / 2);
    let count = countAndMerge(start, middle) + countAndMerge(middle, end);
    let lowerIndex = middle;
    let upperIndex = middle;
    let right = middle;
    let output = start;

    for (let left = start; left < middle; left++) {
      while (lowerIndex < end && prefixes[lowerIndex] - prefixes[left] < lower) lowerIndex++;
      while (upperIndex < end && prefixes[upperIndex] - prefixes[left] <= upper) upperIndex++;
      count += upperIndex - lowerIndex;
      while (right < end && prefixes[right] < prefixes[left]) {
        buffer[output++] = prefixes[right++];
      }
      buffer[output++] = prefixes[left];
    }
    while (right < end) buffer[output++] = prefixes[right++];
    for (let index = start; index < end; index++) prefixes[index] = buffer[index];
    return count;
  }

  return countAndMerge(0, prefixes.length);
}
