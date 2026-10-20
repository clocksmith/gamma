function solve(values) {
  let count = 1, count2 = 1;
  for (let value = 1; value <= values; value++) {
    [count, count2] = [
      count2,
      count + count2
    ];
  }
  return count;
}
