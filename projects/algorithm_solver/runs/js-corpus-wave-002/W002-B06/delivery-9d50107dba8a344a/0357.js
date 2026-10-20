function countNumbersWithUniqueDigits(n) {
  if (n === 0) return 1;
  let count = 10;
  let newNumbers = 9;
  let choices = 9;

  for (let digits = 2; digits <= Math.min(n, 10); digits++) {
    newNumbers *= choices;
    count += newNumbers;
    choices--;
  }
  return count;
}
