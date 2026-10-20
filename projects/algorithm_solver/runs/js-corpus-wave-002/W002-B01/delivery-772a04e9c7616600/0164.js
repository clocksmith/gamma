function maximumGap(nums) {
  if (nums.length < 2) {
    return 0;
  }

  let minimum = nums[0];
  let maximum = nums[0];

  for (const value of nums) {
    minimum = Math.min(minimum, value);
    maximum = Math.max(maximum, value);
  }

  if (minimum === maximum) {
    return 0;
  }

  const bucketSize = Math.max(
    1,
    Math.floor((maximum - minimum) / (nums.length - 1))
  );
  const bucketCount = Math.floor((maximum - minimum) / bucketSize) + 1;
  const bucketMinimum = new Array(bucketCount).fill(Infinity);
  const bucketMaximum = new Array(bucketCount).fill(-Infinity);

  for (const value of nums) {
    const bucket = Math.floor((value - minimum) / bucketSize);
    bucketMinimum[bucket] = Math.min(bucketMinimum[bucket], value);
    bucketMaximum[bucket] = Math.max(bucketMaximum[bucket], value);
  }

  let best = 0;
  let previousMaximum = minimum;

  for (let bucket = 0; bucket < bucketCount; bucket += 1) {
    if (bucketMinimum[bucket] === Infinity) {
      continue;
    }

    best = Math.max(best, bucketMinimum[bucket] - previousMaximum);
    previousMaximum = bucketMaximum[bucket];
  }

  return best;
}
