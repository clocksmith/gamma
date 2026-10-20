function solve(values) {
  let minimum = 0;
  let maximum = Array.from(values).length;
  const result = [];
  for (const value of values) {
    if (value === 'I') {
      result.push(minimum);
      minimum += 1;
    } else {
      result.push(maximum);
      maximum -= 1;
    }
  }
  result.push(minimum);
  return result;
}
