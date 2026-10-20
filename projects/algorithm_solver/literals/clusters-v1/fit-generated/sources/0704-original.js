function lowerBound(values, targetValue) {
  let leftIndex = 0;
  let rightIndex = values.length;
  while (leftIndex < rightIndex) {
    const middleIndex = leftIndex + Math.floor((rightIndex - leftIndex) / 2);
    if (values[middleIndex] < targetValue) {
      leftIndex = middleIndex + 1;
    } else {
      rightIndex = middleIndex;
    }
  }
  return leftIndex;
}
function findSortedIndex(values, targetValue) {
  const insertionIndex = lowerBound(values, targetValue);
  if (insertionIndex < values.length && values[insertionIndex] === targetValue) {
    return insertionIndex;
  }
  return -1;
}
class Solution {
  search(nums, target) {
    return findSortedIndex(nums, target);
  }
}
