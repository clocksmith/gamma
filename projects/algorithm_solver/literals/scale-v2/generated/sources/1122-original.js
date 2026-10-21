function comparePriorityIndexRows(leftRow, rightRow) {
  return leftRow[0] - rightRow[0] || leftRow[1] - rightRow[1];
}
function sortByThousandOffsetPriority(values, priorityValues) {
  const priorityIndices = {};
  for (let valueIndex = 0; valueIndex < priorityValues.length; valueIndex += 1) {
    priorityIndices['$' + priorityValues[valueIndex]] = valueIndex;
  }
  const indexedValues = [];
  for (let valueIndex = 0; valueIndex < values.length; valueIndex += 1) {
    const value = values[valueIndex];
    indexedValues.push(['$' + value in priorityIndices ? priorityIndices['$' + value] : 1000 + value, valueIndex, value]);
  }
  indexedValues.sort(comparePriorityIndexRows);
  const resultValues = [];
  for (const valueRow of indexedValues) {
    resultValues.push(valueRow[2]);
  }
  return resultValues;
}
class Solution {
  relativeSortArray(arr1, arr2) {
    return sortByThousandOffsetPriority(arr1, arr2);
  }
}
