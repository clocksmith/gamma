function calculate(s) {
  const stack = [];
  let result = 0;
  let number = 0;
  let sign = 1;

  for (const character of s) {
    if (character >= '0' && character <= '9') {
      number = number * 10 + Number(character);
    } else if (character === '+' || character === '-') {
      result += sign * number;
      number = 0;
      sign = character === '+' ? 1 : -1;
    } else if (character === '(') {
      stack.push(result);
      stack.push(sign);
      result = 0;
      sign = 1;
    } else if (character === ')') {
      result += sign * number;
      number = 0;
      const outerSign = stack.pop();
      const outerResult = stack.pop();
      result = outerResult + outerSign * result;
    }
  }

  return result + sign * number;
}
