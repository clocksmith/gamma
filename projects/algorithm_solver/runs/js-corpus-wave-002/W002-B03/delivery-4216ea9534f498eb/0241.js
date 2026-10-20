function diffWaysToCompute(expression) {
  const memo = new Map();
  function solve(text) {
    if (memo.has(text)) return memo.get(text);
    const result = [];
    for (let i = 0; i < text.length; i++) {
      const op = text[i];
      if (op !== '+' && op !== '-' && op !== '*') continue;
      for (const left of solve(text.slice(0, i))) for (const right of solve(text.slice(i + 1))) {
        result.push(op === '+' ? left + right : op === '-' ? left - right : left * right);
      }
    }
    if (!result.length) result.push(Number(text));
    memo.set(text, result);
    return result;
  }
  return solve(expression);
}
