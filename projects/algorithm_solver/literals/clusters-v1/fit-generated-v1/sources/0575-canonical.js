function solve(values) {
  const count = helper(values);
  const value = Math.floor(values.length / 2);
  if (count < value) {
    return count;
  }
  return value;
}
function helper(values2) {
  const value2 = {};
  let count2 = 0;
  for (const value3 of values2) {
    if (value2[value3] !== true) {
      value2[value3] = true;
      count2 += 1;
    }
  }
  return count2;
}
