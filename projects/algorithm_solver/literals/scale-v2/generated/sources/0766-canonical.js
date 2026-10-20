function solve(values) {
  const count = values.length;
  const count2 = values[0].length;
  for (let index = 1; index < count; index += 1) {
    for (let index2 = 1; index2 < count2; index2 += 1) {
      if (values[index][index2] !== values[index - 1][index2 - 1]) {
        return false;
      }
    }
  }
  return true;
}
