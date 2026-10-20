function solve(values) {
  let count = 0;
  let size = 0;
  for (const value of values) {
    if (value === 'A') {
      count += 1;
      if (count >= 2) {
        return false;
      }
    }
    if (value === 'L') {
      size += 1;
      if (size >= 3) {
        return false;
      }
    } else {
      size = 0;
    }
  }
  return true;
}
