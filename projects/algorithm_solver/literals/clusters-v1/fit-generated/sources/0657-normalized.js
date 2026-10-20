function returnsToOrigin(text) {
  let horizontalPosition = 0;
  let verticalPosition = 0;
  for (const character of text) {
    if (character === 'U') {
      verticalPosition += 1;
    } else if (character === 'D') {
      verticalPosition -= 1;
    } else if (character === 'L') {
      horizontalPosition -= 1;
    } else if (character === 'R') {
      horizontalPosition += 1;
    }
  }
  return horizontalPosition === 0 && verticalPosition === 0;
}
function solve(moves) {
  return returnsToOrigin(moves);
}
