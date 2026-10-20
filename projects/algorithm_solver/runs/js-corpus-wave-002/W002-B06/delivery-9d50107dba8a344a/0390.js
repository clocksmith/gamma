function lastRemaining(n) {
  let first = 1;
  let step = 1;
  let count = n;
  let leftToRight = true;

  while (count > 1) {
    if (leftToRight || count % 2 === 1) first += step;
    count = Math.floor(count / 2);
    step *= 2;
    leftToRight = !leftToRight;
  }
  return first;
}
