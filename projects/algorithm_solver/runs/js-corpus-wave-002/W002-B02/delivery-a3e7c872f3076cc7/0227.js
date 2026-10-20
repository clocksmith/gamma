function calculate(s) {
  const values = [];
  let number = 0;
  let operation = '+';

  for (let index = 0; index <= s.length; index += 1) {
    const character = index < s.length ? s[index] : '+';

    if (character >= '0' && character <= '9') {
      number = number * 10 + Number(character);
      continue;
    }
    if (character === ' ') {
      continue;
    }

    if (operation === '+') {
      values.push(number);
    } else if (operation === '-') {
      values.push(-number);
    } else if (operation === '*') {
      values.push(values.pop() * number);
    } else {
      values.push(Math.trunc(values.pop() / number));
    }

    operation = character;
    number = 0;
  }

  return values.reduce((total, value) => total + value, 0);
}
