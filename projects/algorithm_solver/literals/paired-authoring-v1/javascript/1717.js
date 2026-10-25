function removePair(characters, first, second, value) {
  const stack = [];
  let score = 0;
  for (const character of characters) {
    if (stack.length > 0 && stack[stack.length - 1] === first && character === second) {
      stack.pop();
      score += value;
    } else {
      stack.push(character);
    }
  }
  return [stack, score];
}


class Solution {
  maximumGain(s, x, y) {
    const characters = Array.from(s);
    let remaining;
    let firstScore;
    let secondScore;
    if (x >= y) {
      [remaining, firstScore] = removePair(characters, "a", "b", x);
      [, secondScore] = removePair(remaining, "b", "a", y);
    } else {
      [remaining, firstScore] = removePair(characters, "b", "a", y);
      [, secondScore] = removePair(remaining, "a", "b", x);
    }
    return firstScore + secondScore;
  }
}
