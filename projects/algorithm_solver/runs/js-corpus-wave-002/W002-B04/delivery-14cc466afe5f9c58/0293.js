function generatePossibleNextMoves(currentState) {
  const result = [];
  for (let i = 0; i + 1 < currentState.length; i++) {
    if (currentState[i] === '+' && currentState[i + 1] === '+') {
      result.push(currentState.slice(0, i) + '--' + currentState.slice(i + 2));
    }
  }
  return result;
}
