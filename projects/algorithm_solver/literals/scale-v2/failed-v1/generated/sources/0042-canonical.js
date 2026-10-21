function solve(values) {
  let index = 0;
  let index2 = values.length - 1;
  let maximum = 0;
  let maximum2 = 0;
  let value = 0;
  while (index < index2) {
    if (values[index] <= values[index2]) {
      maximum = Math.max(maximum, values[index]);
      value += maximum - values[index];
      index++;
    } else {
      maximum2 = Math.max(maximum2, values[index2]);
      value += maximum2 - values[index2];
      index2--;
    }
  }
  return value;
}
