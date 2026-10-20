function solve(values) {
  const result = [];
  let index = 0;
  let index2 = values.length;
  while (index < index2) {
    const left = values[index] * values[index];
    const right = values[index2 - 1] * values[index2 - 1];
    if (left > right) {
      result.push(left);
      index += 1;
    } else {
      result.push(right);
      index2 -= 1;
    }
  }
  result.reverse();
  return result;
}
