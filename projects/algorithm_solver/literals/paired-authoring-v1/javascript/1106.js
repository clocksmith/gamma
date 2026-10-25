class Solution {
  parseBoolExpr(expression) {
    const stack = [];
    for (const token of expression) {
      if (token === ",") {
        continue;
      }
      if (token !== ")") {
        stack.push(token);
        continue;
      }
      let seenTrue = false;
      let seenFalse = false;
      while (stack[stack.length - 1] !== "(") {
        const value = stack.pop();
        if (value === "t") {
          seenTrue = true;
        } else {
          seenFalse = true;
        }
      }
      stack.pop();
      const operator = stack.pop();
      let result;
      if (operator === "!") {
        result = !seenTrue;
      } else if (operator === "&") {
        result = !seenFalse;
      } else {
        result = seenTrue;
      }
      stack.push(result ? "t" : "f");
    }
    return stack[0] === "t";
  }
}
