class Solution {
  isMatch(s, p) {
    let previous = new Array(p.length + 1).fill(false);
    previous[0] = true;
    for (let index = 1; index <= p.length; index += 1) {
      if (p[index - 1] === "*") {
        previous[index] = previous[index - 2];
      }
    }

    for (const character of s) {
      const current = new Array(p.length + 1).fill(false);
      for (let index = 1; index <= p.length; index += 1) {
        const symbol = p[index - 1];
        if (symbol === "*") {
          const repeated = p[index - 2];
          const matches = repeated === "." || repeated === character;
          current[index] = current[index - 2] || (matches && previous[index]);
        } else {
          const matches = symbol === "." || symbol === character;
          current[index] = matches && previous[index - 1];
        }
      }
      previous = current;
    }
    return previous[previous.length - 1];
  }
}
