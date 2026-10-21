function solve(values) {
  let index = 0;
  let index2 = values.length - 1;
  let maximum = 0;
  while (index < index2) {
    const value = Math.min(values[index], values[index2]) * (index2 - index);
    maximum = Math.max(maximum, value);
    if (values[index] <= values[index2]) {
      index++;
    } else {
      index2--;
    }
  }
  return maximum;
}
