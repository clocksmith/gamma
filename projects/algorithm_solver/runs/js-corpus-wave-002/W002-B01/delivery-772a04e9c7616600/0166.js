function fractionToDecimal(numerator, denominator) {
  if (numerator === 0) {
    return '0';
  }

  const negative = (numerator < 0) !== (denominator < 0);
  const dividend = Math.abs(numerator);
  const divisor = Math.abs(denominator);
  const integerPart = Math.floor(dividend / divisor);
  let remainder = dividend % divisor;
  let result = `${negative ? '-' : ''}${integerPart}`;

  if (remainder === 0) {
    return result;
  }

  result += '.';
  const digits = [];
  const seen = new Map();

  while (remainder !== 0) {
    if (seen.has(remainder)) {
      digits.splice(seen.get(remainder), 0, '(');
      digits.push(')');
      break;
    }

    seen.set(remainder, digits.length);
    remainder *= 10;
    digits.push(String(Math.floor(remainder / divisor)));
    remainder %= divisor;
  }

  return result + digits.join('');
}
