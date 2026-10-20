function evalRPN(tokens) {
  const stack = [];
  const operators = new Set(['+', '-', '*', '/']);

  for (const token of tokens) {
    if (!operators.has(token)) {
      stack.push(Number(token));
      continue;
    }

    const right = stack.pop();
    const left = stack.pop();

    if (token === '+') {
      stack.push(left + right);
    } else if (token === '-') {
      stack.push(left - right);
    } else if (token === '*') {
      stack.push(left * right);
    } else {
      stack.push(Math.trunc(left / right));
    }
  }

  return stack.pop();
}
