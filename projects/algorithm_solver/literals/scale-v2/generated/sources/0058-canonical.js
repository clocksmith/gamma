function solve(values) {
  let index = values.length - 1, size = 0;
  while (index >= 0 && values[index] === ' ') {
    index--;
  }
  while (index >= 0 && values[index] !== ' ') {
    size++;
    index--;
  }
  return size;
}
