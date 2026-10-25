class Solution {
  generateParenthesis(n) {
    const combinations = [];
    const path = [];

    function collect(openCount, closeCount) {
      if (closeCount === n) {
        combinations.push(path.join(""));
        return;
      }
      if (openCount < n) {
        path.push("(");
        collect(openCount + 1, closeCount);
        path.pop();
      }
      if (closeCount < openCount) {
        path.push(")");
        collect(openCount, closeCount + 1);
        path.pop();
      }
    }

    collect(0, 0);
    return combinations;
  }
}
