class Solution {
  expand(expression) {
    let results = [""];
    let index = 0;
    while (index < expression.length) {
      const choices = [];
      if (expression[index] === "{") {
        const end = expression.indexOf("}", index + 1);
        choices.push(...expression.slice(index + 1, end).split(","));
        index = end + 1;
      } else {
        choices.push(expression[index]);
        index += 1;
      }
      const expanded = [];
      for (const prefix of results) {
        for (const character of choices) {
          expanded.push(prefix + character);
        }
      }
      results = expanded;
    }
    return results.sort();
  }
}
