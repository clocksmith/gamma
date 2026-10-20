function solve(values, other) {
  const value = indexTextPositions(other);
  let index = values.length + other.length;
  let result = [];
  for (let index2 = 0; index2 < values.length; index2 += 1) {
    const value2 = values[index2];
    const key = encodeTextKey(value2);
    if (key in value) {
      const index3 = value[key];
      const index4 = index2 + index3;
      if (index4 < index) {
        index = index4;
        result = [value2];
      } else if (index4 === index) {
        result.push(value2);
      }
    }
  }
  return result;
}
function helper(values2) {
  return '$' + values2;
}
function helper2(values3) {
  const value3 = {};
  for (let index5 = 0; index5 < values3.length; index5 += 1) {
    const key2 = encodeTextKey(values3[index5]);
    value3[key2] = index5;
  }
  return value3;
}
