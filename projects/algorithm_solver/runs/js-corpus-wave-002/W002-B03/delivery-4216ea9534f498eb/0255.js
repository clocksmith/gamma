function verifyPreorder(preorder) {
  const stack = [];
  let lower = -Infinity;
  for (const value of preorder) {
    if (value <= lower) return false;
    while (stack.length && value > stack[stack.length - 1]) lower = stack.pop();
    if (stack.length && value === stack[stack.length - 1]) return false;
    stack.push(value);
  }
  return true;
}
