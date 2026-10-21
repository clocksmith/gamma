function baseballScore(operations) {
  const scoreStack = [];
  for (const operation of operations) {
    if (operation === '+') {
      scoreStack.push(scoreStack[scoreStack.length - 1] + scoreStack[scoreStack.length - 2]);
    } else if (operation === 'D') {
      scoreStack.push(scoreStack[scoreStack.length - 1] * 2);
    } else if (operation === 'C') {
      scoreStack.pop();
    } else {
      scoreStack.push(+operation);
    }
  }
  let totalScore = 0;
  for (const scoreValue of scoreStack) {
    totalScore += scoreValue;
  }
  return totalScore;
}
class Solution {
  calPoints(operations) {
    return baseballScore(operations);
  }
}
