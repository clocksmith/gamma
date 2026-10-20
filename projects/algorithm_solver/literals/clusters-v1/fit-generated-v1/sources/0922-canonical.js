function solve(values) {
  let index = 1;
  for (let index2 = 0; index2 < values.length; index2 += 2) {
    if (values[index2] % 2 !== 0) {
      while (index < values.length && values[index] % 2 !== 0) {
        index += 2;
      }
      if (index >= values.length) {
        throw 'parity count mismatch';
      }
      const value = values[index2];
      values[index2] = values[index];
      values[index] = value;
    }
  }
  return values;
}
