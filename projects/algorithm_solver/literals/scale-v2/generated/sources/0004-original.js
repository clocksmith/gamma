function findMedianSortedArrays(nums1, nums2) {
  let shortValues = nums1;
  let longValues = nums2;

  // Binary-search the shorter array.
  if (shortValues.length > longValues.length) {
    [shortValues, longValues] = [longValues, shortValues];
  }
  const shortLength = shortValues.length;
  const longLength = longValues.length;
  if (shortLength + longLength === 0) {
    throw new RangeError('Both arrays are empty');
  }
  const leftSize = Math.floor((shortLength + longLength + 1) / 2);
  let lowerBound = 0;
  let upperBound = shortLength;
  while (lowerBound <= upperBound) {
    const shortPartition = Math.floor((lowerBound + upperBound) / 2);
    const longPartition = leftSize - shortPartition;
    const shortLeftValue = shortPartition === 0 ? -Infinity : shortValues[shortPartition - 1];
    const shortRightValue = shortPartition === shortLength ? Infinity : shortValues[shortPartition];
    const longLeftValue = longPartition === 0 ? -Infinity : longValues[longPartition - 1];
    const longRightValue = longPartition === longLength ? Infinity : longValues[longPartition];
    if (shortLeftValue <= longRightValue && longLeftValue <= shortRightValue) {
      const lower = Math.max(shortLeftValue, longLeftValue);
      if ((shortLength + longLength) % 2 === 1) {
        return lower;
      }
      const upper = Math.min(shortRightValue, longRightValue);
      return lower / 2 + upper / 2;
    }
    if (shortLeftValue > longRightValue) {
      upperBound = shortPartition - 1;
    } else {
      lowerBound = shortPartition + 1;
    }
  }
  throw new RangeError('Inputs must be sorted in ascending order');
}
