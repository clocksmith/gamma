function solve(values) {
  const result = [];
  let value = 0;
  for (const value2 of values) {
    value = ((value * 2 | value2) % 5 + 5) % 5;
    result.push(value === 0);
  }
  return result;
}
