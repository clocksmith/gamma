function solve(values) {
  let index = 0;
  let index2 = 0;
  for (const value of values) {
    if (value === 'U') {
      index2 += 1;
    } else if (value === 'D') {
      index2 -= 1;
    } else if (value === 'L') {
      index -= 1;
    } else if (value === 'R') {
      index += 1;
    }
  }
  return index === 0 && index2 === 0;
}
