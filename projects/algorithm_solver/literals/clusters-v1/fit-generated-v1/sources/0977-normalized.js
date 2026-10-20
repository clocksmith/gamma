function sortedSquareValues(values) {
  const resultValues = [];
  let leftIndex = 0;
  let rightBound = values.length;
  while (leftIndex < rightBound) {
    const leftSquare = values[leftIndex] * values[leftIndex];
    const rightSquare = values[rightBound - 1] * values[rightBound - 1];
    if (leftSquare > rightSquare) {
      resultValues.push(leftSquare);
      leftIndex += 1;
    } else {
      resultValues.push(rightSquare);
      rightBound -= 1;
    }
  }
  resultValues.reverse();
  return resultValues;
}
function solve(nums) {
  return sortedSquareValues(nums);
}
