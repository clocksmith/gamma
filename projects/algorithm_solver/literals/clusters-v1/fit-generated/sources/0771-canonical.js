function solve(values, other) {
  const key = {};
  for (const value of values) {
    const key2 = encodeTextKey(value);
    key[key2] = true;
  }
  let count = 0;
  for (const value2 of other) {
    const key3 = encodeTextKey(value2);
    if (key3 in key) {
      count += 1;
    }
  }
  return count;
}
function helper(values2) {
  return '$' + values2;
}
