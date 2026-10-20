function findStrobogrammatic(n) {
  function build(length) {
    if (length === 0) return [''];
    if (length === 1) return ['0', '1', '8'];
    const result = [];
    for (const middle of build(length - 2)) for (const [a, b] of [['0', '0'], ['1', '1'], ['6', '9'], ['8', '8'], ['9', '6']]) {
      if (length === n && a === '0') continue;
      result.push(a + middle + b);
    }
    return result;
  }
  return build(n);
}
