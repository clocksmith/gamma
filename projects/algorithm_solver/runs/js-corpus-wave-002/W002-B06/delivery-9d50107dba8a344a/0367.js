function isPerfectSquare(num) {
  if (!Number.isInteger(num) || num < 0) return false;
  let low = 0;
  let high = Math.min(num, 46341);
  while (low <= high) {
    const middle = low + Math.floor((high - low) / 2);
    const squared = middle * middle;
    if (squared === num) return true;
    if (squared < num) low = middle + 1;
    else high = middle - 1;
  }
  return false;
}
