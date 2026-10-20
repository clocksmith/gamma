function minArea(image, x, y) {
  const height = image.length, width = image[0].length;
  const black = (row, col) => image[row][col] === '1' || image[row][col] === 1;
  function rowHasBlack(row) { for (let col = 0; col < width; col++) if (black(row, col)) return true; return false; }
  function colHasBlack(col) { for (let row = 0; row < height; row++) if (black(row, col)) return true; return false; }
  function firstTrue(left, right, predicate) {
    while (left < right) { const mid = Math.floor((left + right) / 2); if (predicate(mid)) right = mid; else left = mid + 1; }
    return left;
  }
  function firstFalse(left, right, predicate) {
    while (left < right) { const mid = Math.floor((left + right) / 2); if (predicate(mid)) left = mid + 1; else right = mid; }
    return left;
  }
  const top = firstTrue(0, x + 1, rowHasBlack);
  const bottom = firstFalse(x, height, rowHasBlack);
  const left = firstTrue(0, y + 1, colHasBlack);
  const right = firstFalse(y, width, colHasBlack);
  return (bottom - top) * (right - left);
}
