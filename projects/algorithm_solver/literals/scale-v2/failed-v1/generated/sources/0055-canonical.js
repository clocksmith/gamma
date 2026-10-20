function solve(values) {
  let index = 0;
  for (let index2 = 0; index2 < values.length; index2++) {
    if (index2 > index) {
      return false;
    }
    index = Math.max(index, index2 + values[index2]);
  }
  return true;
}
