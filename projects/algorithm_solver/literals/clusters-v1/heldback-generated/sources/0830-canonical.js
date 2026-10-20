function solve(values) {
  let count = 0;
  let value = 0;
  let left = '';
  const result = [];
  for (const value2 of values) {
    if (count > 0 && value2 !== left) {
      if (count - value >= 3) {
        result.push([
          value,
          count - 1
        ]);
      }
      value = count;
    }
    left = value2;
    count += 1;
  }
  if (count - value >= 3) {
    result.push([
      value,
      count - 1
    ]);
  }
  return result;
}
