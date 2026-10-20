function shortestDegreeSpan(values) {
  if (values.length === 0) {
    return 0;
  }
  let minimumValue = values[0];
  let maximumValue = values[0];
  for (const value of values) {
    if (value < minimumValue) {
      minimumValue = value;
    }
    if (value > maximumValue) {
      maximumValue = value;
    }
  }
  const countsByOffset = new Array(maximumValue - minimumValue + 1).fill(0);
  const firstIndicesByOffset = new Array(countsByOffset.length).fill(-1);
  let degreeCount = 0;
  let shortestLength = values.length;
  for (let valueIndex = 0; valueIndex < values.length; valueIndex += 1) {
    const valueOffset = values[valueIndex] - minimumValue;
    if (firstIndicesByOffset[valueOffset] === -1) {
      firstIndicesByOffset[valueOffset] = valueIndex;
    }
    countsByOffset[valueOffset] += 1;
    const spanLength = valueIndex - firstIndicesByOffset[valueOffset] + 1;
    if (countsByOffset[valueOffset] > degreeCount) {
      degreeCount = countsByOffset[valueOffset];
      shortestLength = spanLength;
    } else if (countsByOffset[valueOffset] === degreeCount && spanLength < shortestLength) {
      shortestLength = spanLength;
    }
  }
  return shortestLength;
}
function solve(nums) {
  return shortestDegreeSpan(nums);
}
