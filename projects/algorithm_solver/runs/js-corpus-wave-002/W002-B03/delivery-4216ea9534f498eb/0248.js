function strobogrammaticInRange(low, high) {
  let count = 0;
  function visit(chars, left, right) {
    if (left > right) {
      const value = chars.join('');
      if ((value.length > low.length || value >= low) && (value.length < high.length || value <= high)) count++;
      return;
    }
    const pairs = left === right ? [['0', '0'], ['1', '1'], ['8', '8']] : [['0', '0'], ['1', '1'], ['6', '9'], ['8', '8'], ['9', '6']];
    for (const [a, b] of pairs) {
      if (left === 0 && right > left && a === '0') continue;
      chars[left] = a; chars[right] = b;
      visit(chars, left + 1, right - 1);
    }
  }
  for (let n = low.length; n <= high.length; n++) visit(Array(n), 0, n - 1);
  return count;
}
