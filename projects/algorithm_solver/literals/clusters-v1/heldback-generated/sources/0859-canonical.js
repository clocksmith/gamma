function solve(values, other) {
  const left = Array.from(values);
  const right = Array.from(other);
  if (left.length !== right.length) {
    return false;
  }
  const items = {};
  let value = false;
  const value2 = [];
  for (let index3 = 0; index3 < left.length; index3 += 1) {
    const value3 = left[index3];
    const key = helper(value3);
    if (items[key] === true) {
      value = true;
    }
    items[key] = true;
    if (value3 !== right[index3]) {
      value2.push(index3);
      if (value2.length > 2) {
        return false;
      }
    }
  }
  if (value2.length === 0) {
    return value;
  }
  if (value2.length !== 2) {
    return false;
  }
  const index = value2[0];
  const index2 = value2[1];
  return left[index] === right[index2] && left[index2] === right[index];
}
function helper(values2) {
  return '$' + values2;
}
