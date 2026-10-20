function solve(values) {
  let result = '';
  for (const value of values) {
    if (!'aeiou'.includes(value)) {
      result += value;
    }
  }
  return result;
}
