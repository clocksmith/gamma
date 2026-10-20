function solve(values) {
  let value = true;
  let value2 = true;
  for (let index = 1; index < values.length; index += 1) {
    if (values[index - 1] > values[index]) {
      value = false;
    }
    if (values[index - 1] < values[index]) {
      value2 = false;
    }
  }
  return value || value2;
}
