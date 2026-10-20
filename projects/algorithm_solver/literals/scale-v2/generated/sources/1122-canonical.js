function solve(values, other) {
  const value = {};
  for (let index2 = 0; index2 < other.length; index2 += 1) {
    value['$' + other[index2]] = index2;
  }
  const index = [];
  for (let index3 = 0; index3 < values.length; index3 += 1) {
    const value2 = values[index3];
    index.push([
      '$' + value2 in value ? value['$' + value2] : 1000 + value2,
      index3,
      value2
    ]);
  }
  index.sort(helper);
  const result = [];
  for (const value3 of index) {
    result.push(value3[2]);
  }
  return result;
}
function helper(values2, other2) {
  return values2[0] - other2[0] || values2[1] - other2[1];
}
