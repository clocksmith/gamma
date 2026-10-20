function solve(values) {
  let size = 1;
  let size2 = 1;
  for (let index = 1; index < values.length; index += 1) {
    if (values[index - 1] < values[index]) {
      size += 1;
      if (size > size2) {
        size2 = size;
      }
    } else {
      size = 1;
    }
  }
  return size2;
}
