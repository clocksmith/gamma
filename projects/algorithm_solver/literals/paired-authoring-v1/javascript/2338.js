function multiplyMod(first, second, modulus) {
  let result = 0;
  while (second > 0) {
    if (second % 2 === 1) {
      result = (result + first) % modulus;
    }
    first = (first + first) % modulus;
    second = Math.floor(second / 2);
  }
  return result;
}


class Solution {
  idealArrays(n, maxValue) {
    const modulus = 1000000007;
    let exponentLimit = 0;
    let power = 1;
    while (power * 2 <= maxValue) {
      power *= 2;
      exponentLimit += 1;
    }
    const combinations = Array(exponentLimit + 1).fill(1);
    for (let position = 1; position < n; position += 1) {
      for (let exponent = 1; exponent <= exponentLimit; exponent += 1) {
        combinations[exponent] = (combinations[exponent] + combinations[exponent - 1]) % modulus;
      }
    }
    const smallest = Array.from({length: maxValue + 1}, (_, index) => index);
    let prime = 2;
    while (prime * prime <= maxValue) {
      if (smallest[prime] === prime) {
        for (let multiple = prime * prime; multiple <= maxValue; multiple += prime) {
          if (smallest[multiple] === multiple) {
            smallest[multiple] = prime;
          }
        }
      }
      prime += 1;
    }
    let answer = 0;
    for (let value = 1; value <= maxValue; value += 1) {
      let remaining = value;
      let ways = 1;
      while (remaining > 1) {
        const factor = smallest[remaining];
        let exponent = 0;
        while (remaining % factor === 0) {
          remaining /= factor;
          exponent += 1;
        }
        ways = multiplyMod(ways, combinations[exponent], modulus);
      }
      answer = (answer + ways) % modulus;
    }
    return answer;
  }
}
