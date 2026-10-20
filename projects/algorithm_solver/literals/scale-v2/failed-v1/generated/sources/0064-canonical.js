function solve(values) {
  const count = values.length, count2 = values[0].length;
  const value = Array(count2).fill(Infinity);
  value[0] = 0;
  for (let index = 0; index < count; index++) {
    for (let index2 = 0; index2 < count2; index2++) {
      value[index2] = values[index][index2] + Math.min(value[index2], index2 ? value[index2 - 1] : Infinity);
    }
  }
  return value[count2 - 1];
}
