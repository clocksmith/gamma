function countDistinctValues(values) {
  const seenByValue = {};
  let distinctCount = 0;
  for (const value of values) {
    if (seenByValue[value] !== true) {
      seenByValue[value] = true;
      distinctCount += 1;
    }
  }
  return distinctCount;
}
function maximumCandyTypeCount(values) {
  const distinctCount = countDistinctValues(values);
  const candyLimit = Math.floor(values.length / 2);
  if (distinctCount < candyLimit) {
    return distinctCount;
  }
  return candyLimit;
}
function solve(candyType) {
  return maximumCandyTypeCount(candyType);
}
